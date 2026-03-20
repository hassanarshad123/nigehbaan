"""Supreme Court of Pakistan (SCP) scraper.

Scrapes the Supreme Court judgment search portal hosted on the
NADRA infrastructure. The portal provides a web-based search
interface for decided cases.

Strategy:
    1. POST search queries to the judgment search form
    2. Parse HTML result tables for case listings
    3. Download judgment PDFs for relevant cases
    4. Extract metadata from case listing and judgment text

URL: https://supremecourt.nadra.gov.pk/judgement-search/
Tool: Requests + BeautifulSoup (standard HTML, no JS rendering needed)
Schedule: Weekly (0 3 * * 1)
Priority: P1 — Supreme Court decisions set precedent
"""

from typing import Any
from urllib.parse import urljoin

import logging

from bs4 import BeautifulSoup

from data.scrapers.courts.base_court_scraper import BaseCourtScraper

logger = logging.getLogger(__name__)

# Case types relevant to criminal / trafficking matters
CRIMINAL_CASE_TYPES: list[str] = [
    "Criminal Appeal",
    "Criminal Petition",
    "Criminal Miscellaneous Application",
    "Criminal Review Petition",
    "Jail Petition",
    "Human Rights Case",
]


class SCPScraper(BaseCourtScraper):
    """Scraper for Supreme Court of Pakistan judgments.

    The SCP portal on NADRA uses a standard HTML form for case
    search. Results are returned as HTML tables that can be parsed
    with BeautifulSoup. Judgment PDFs are downloadable via direct links.

    Attributes:
        name: Scraper identifier.
        court_name: Full court name for metadata.
        source_url: NADRA judgment search portal URL.
        schedule: Weekly cron expression.
    """

    name: str = "scp"
    court_name: str = "Supreme Court of Pakistan"
    source_url: str = "https://supremecourt.nadra.gov.pk/judgement-search/"
    schedule: str = "0 3 * * 1"
    priority: str = "P1"

    async def _fetch_results_page(
        self,
        year: int,
        case_type: str,
        page: int = 1,
    ) -> str:
        """Fetch a single page of search results from the SCP portal.

        Args:
            year: Year to search.
            case_type: Case type string (e.g. 'Criminal Appeal').
            page: Page number for paginated results.

        Returns:
            Raw HTML response text.
        """
        form_data: dict[str, Any] = {
            "year": str(year),
            "case_type": case_type,
            "page": str(page),
        }
        response = await self.fetch(
            self.source_url,
            method="POST",
            data=form_data,
        )
        return response.text

    def _parse_results_table(self, html: str) -> list[dict[str, Any]]:
        """Parse the HTML results table into case reference dicts.

        Args:
            html: Raw HTML containing the results table.

        Returns:
            List of case reference dicts extracted from table rows.
        """
        soup = BeautifulSoup(html, "html.parser")
        cases: list[dict[str, Any]] = []

        table = soup.find("table", class_="table") or soup.find("table")
        if not table:
            return cases

        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header row
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            # Extract PDF link if present
            pdf_url = ""
            link_tag = row.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                pdf_url = urljoin(self.source_url, href)

            case_number = cells[0].get_text(strip=True)
            parties = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            date_decided = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            result = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            # Extract year from case number or date
            year_val = ""
            if "/" in case_number:
                parts = case_number.split("/")
                year_val = parts[-1].strip()
            if not year_val and date_decided:
                # Try last 4 chars as year
                potential = date_decided[-4:]
                if potential.isdigit():
                    year_val = potential

            cases.append({
                "case_number": case_number,
                "year": year_val,
                "parties": parties,
                "title": parties,
                "date_decided": date_decided,
                "result": result,
                "pdf_url": pdf_url,
                "court": self.court_name,
            })

        return cases

    def _has_next_page(self, html: str) -> bool:
        """Check whether pagination indicates more pages exist.

        Args:
            html: HTML response text.

        Returns:
            True if a 'next' page link is found.
        """
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.find("a", string=lambda t: t and "next" in t.lower())
        if next_link:
            return True
        # Also check for pagination li with 'next' class
        next_li = soup.find("li", class_="next")
        if next_li and next_li.find("a"):
            return True
        return False

    async def search_cases(
        self, year: int, case_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Search SCP judgment portal by year and case type.

        Submits a POST request to the NADRA search form with
        the specified parameters and parses the result table.

        Args:
            year: Year to search for decided cases.
            case_type: Optional case type filter (e.g., 'Criminal
                Appeal', 'Criminal Petition').

        Returns:
            List of case reference dicts from search results.
        """
        all_cases: list[dict[str, Any]] = []
        types_to_search = [case_type] if case_type else CRIMINAL_CASE_TYPES

        for ct in types_to_search:
            page = 1
            max_pages = 50  # safety limit
            try:
                while page <= max_pages:
                    html = await self._fetch_results_page(year, ct, page)
                    page_cases = self._parse_results_table(html)
                    if not page_cases:
                        break
                    all_cases.extend(page_cases)
                    if not self._has_next_page(html):
                        break
                    page += 1
            except Exception as exc:
                logger.warning(
                    "[%s] Error searching case_type=%s year=%d page=%d: %s",
                    self.name, ct, year, page, exc,
                )
                continue

        logger.info(
            "[%s] Found %d total cases for year %d",
            self.name, len(all_cases), year,
        )
        return all_cases

    async def download_judgment(
        self, case_ref: dict[str, Any]
    ) -> bytes | None:
        """Download SCP judgment PDF.

        SCP judgments are typically available as direct PDF download
        links from the search results page. Delegates to the base
        class implementation which fetches from pdf_url.

        Args:
            case_ref: Case reference dict with download URL.

        Returns:
            Raw PDF bytes or None if unavailable.
        """
        return await super().download_judgment(case_ref)

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the SCP scraping pipeline.

        Searches for cases across recent years, filters for
        relevant PPC sections, downloads judgments, and extracts
        metadata.

        Returns:
            List of case records with metadata and PDF references.
        """
        logger.info("[%s] Starting SCP scrape", self.name)
        results = await self.scrape_year_range()
        logger.info("[%s] SCP scrape complete: %d records", self.name, len(results))
        return results

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an SCP case record.

        Args:
            record: A case record dictionary.

        Returns:
            True if case_number, year, and court are present.
        """
        required_fields = ["case_number", "year", "court"]
        return all(record.get(f) for f in required_fields)
