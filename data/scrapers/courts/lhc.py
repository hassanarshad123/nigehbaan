"""Lahore High Court (LHC) scraper.

Scrapes the Lahore High Court reported judgments portal for
trafficking and child abuse cases. LHC covers Punjab province,
which has the highest population and the most reported cases.

Strategy:
    1. Search the reported judgments portal by PPC section
    2. Parse judgment listing pages
    3. Download judgment PDFs
    4. Extract case metadata from listings

URL: https://data.lhc.gov.pk/reported_judgments/
Tool: Requests + BeautifulSoup (standard HTML)
Schedule: Weekly (0 3 * * 2)
Priority: P1 — Punjab has highest case volume
"""

from typing import Any
from urllib.parse import urljoin

import logging

from bs4 import BeautifulSoup

from data.scrapers.courts.base_court_scraper import (
    BaseCourtScraper,
    PPC_SECTIONS_OF_INTEREST,
)

logger = logging.getLogger(__name__)


class LHCScraper(BaseCourtScraper):
    """Scraper for Lahore High Court reported judgments.

    The LHC data portal provides a searchable database of reported
    judgments with downloadable PDFs. The interface is standard HTML
    that can be scraped with Requests + BeautifulSoup.

    Attributes:
        name: Scraper identifier.
        court_name: Full court name for metadata.
        source_url: LHC reported judgments portal URL.
        schedule: Weekly on Tuesdays.
    """

    name: str = "lhc"
    court_name: str = "Lahore High Court"
    source_url: str = "https://data.lhc.gov.pk/reported_judgments/"
    schedule: str = "0 3 * * 2"
    priority: str = "P1"

    async def _fetch_search_page(
        self,
        section: str,
        year: int,
        page: int = 1,
    ) -> str:
        """Fetch a search results page for a given PPC section and year.

        Args:
            section: PPC section number to search (e.g. '370').
            year: Year to filter by.
            page: Pagination page number.

        Returns:
            Raw HTML text of the results page.
        """
        params: dict[str, Any] = {
            "section": section,
            "year": str(year),
            "page": str(page),
        }
        response = await self.fetch(
            self.source_url,
            method="GET",
            params=params,
        )
        return response.text

    def _parse_listing(self, html: str) -> list[dict[str, Any]]:
        """Parse LHC judgment listing HTML into case reference dicts.

        Args:
            html: Raw HTML of a results page.

        Returns:
            List of case reference dicts.
        """
        soup = BeautifulSoup(html, "html.parser")
        cases: list[dict[str, Any]] = []

        # Try table-based results first
        table = soup.find("table", class_="table") or soup.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue

                pdf_url = ""
                link_tag = row.find("a", href=True)
                if link_tag:
                    pdf_url = urljoin(self.source_url, link_tag["href"])

                case_number = cells[0].get_text(strip=True)
                title = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                date_decided = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                result = cells[3].get_text(strip=True) if len(cells) > 3 else ""

                year_val = ""
                if "/" in case_number:
                    parts = case_number.split("/")
                    year_val = parts[-1].strip()
                if not year_val and date_decided:
                    potential = date_decided[-4:]
                    if potential.isdigit():
                        year_val = potential

                cases.append({
                    "case_number": case_number,
                    "year": year_val,
                    "parties": title,
                    "title": title,
                    "date_decided": date_decided,
                    "result": result,
                    "pdf_url": pdf_url,
                    "court": self.court_name,
                })
            return cases

        # Fallback: card/div-based listing
        cards = soup.find_all("div", class_="card") or soup.find_all(
            "div", class_="judgment-item"
        )
        for card in cards:
            title_el = card.find(["h5", "h4", "h3", "a"])
            title = title_el.get_text(strip=True) if title_el else ""

            pdf_url = ""
            link = card.find("a", href=True)
            if link:
                pdf_url = urljoin(self.source_url, link["href"])

            # Look for metadata spans or small text
            meta_text = card.get_text(" ", strip=True)
            case_number = ""
            date_decided = ""

            # Try to find case number pattern
            import re
            cn_match = re.search(
                r"([\w\s]+\d+/\d{4})", meta_text
            )
            if cn_match:
                case_number = cn_match.group(1).strip()

            date_match = re.search(
                r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})", meta_text
            )
            if date_match:
                date_decided = date_match.group(1)

            year_val = ""
            if "/" in case_number:
                parts = case_number.split("/")
                year_val = parts[-1].strip()

            cases.append({
                "case_number": case_number,
                "year": year_val,
                "parties": title,
                "title": title,
                "description": meta_text,
                "date_decided": date_decided,
                "pdf_url": pdf_url,
                "court": self.court_name,
            })

        return cases

    def _has_next_page(self, html: str) -> bool:
        """Check if pagination indicates additional pages.

        Args:
            html: HTML response text.

        Returns:
            True if a 'next' page link is found.
        """
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.find("a", string=lambda t: t and "next" in t.lower())
        if next_link:
            return True
        next_li = soup.find("li", class_="next")
        if next_li and next_li.find("a"):
            return True
        # Check for rel="next"
        if soup.find("a", attrs={"rel": "next"}):
            return True
        return False

    async def search_cases(
        self, year: int, case_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Search LHC reported judgments by year and section.

        Queries the LHC portal for judgments involving trafficking-
        related PPC sections within the specified year.

        Args:
            year: Year to search.
            case_type: Optional case type filter.

        Returns:
            List of case reference dicts from search results.
        """
        all_cases: list[dict[str, Any]] = []

        for section in PPC_SECTIONS_OF_INTEREST:
            page = 1
            max_pages = 50
            try:
                while page <= max_pages:
                    html = await self._fetch_search_page(section, year, page)
                    page_cases = self._parse_listing(html)
                    if not page_cases:
                        break
                    all_cases.extend(page_cases)
                    if not self._has_next_page(html):
                        break
                    page += 1
            except Exception as exc:
                logger.warning(
                    "[%s] Error searching section=%s year=%d page=%d: %s",
                    self.name, section, year, page, exc,
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
        """Download LHC judgment PDF.

        Delegates to the base class download_judgment which fetches
        from the pdf_url in the case reference.

        Args:
            case_ref: Case reference dict with PDF download link.

        Returns:
            Raw PDF bytes or None if unavailable.
        """
        return await super().download_judgment(case_ref)

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the LHC scraping pipeline.

        Returns:
            List of case records with metadata.
        """
        logger.info("[%s] Starting LHC scrape", self.name)
        results = await self.scrape_year_range()
        logger.info("[%s] LHC scrape complete: %d records", self.name, len(results))
        return results

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an LHC case record.

        Args:
            record: A case record dictionary.

        Returns:
            True if required fields are present.
        """
        required_fields = ["case_number", "year", "court"]
        return all(record.get(f) for f in required_fields)
