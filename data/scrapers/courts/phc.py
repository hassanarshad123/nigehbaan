"""Peshawar High Court (PHC) scraper.

Scrapes the Peshawar High Court portal for trafficking and child
abuse judgments. PHC covers Khyber Pakhtunkhwa province and has
4 benches (Peshawar, Abbottabad, Mingora, D.I. Khan).

Strategy:
    1. Access the PHC website judgment section
    2. Search by case type and PPC section
    3. Parse result listings
    4. Download judgment PDFs

URL: https://peshawarhighcourt.gov.pk
Tool: Requests + BeautifulSoup
Schedule: Weekly (0 3 * * 4)
Priority: P1 — KP has significant trafficking cases
"""

import re
from typing import Any
from urllib.parse import urljoin

import logging

from bs4 import BeautifulSoup

from data.scrapers.courts.base_court_scraper import (
    BaseCourtScraper,
    PPC_SECTIONS_OF_INTEREST,
)

logger = logging.getLogger(__name__)

# PHC judgment search endpoint
PHC_JUDGMENT_URL = "https://peshawarhighcourt.gov.pk/judgments/"


class PHCScraper(BaseCourtScraper):
    """Scraper for Peshawar High Court judgments.

    PHC has 4 benches covering KP and former FATA. The website
    uses standard HTML that can be parsed with BeautifulSoup.

    Attributes:
        name: Scraper identifier.
        court_name: Full court name.
        source_url: PHC website URL.
        benches: List of PHC bench locations.
    """

    name: str = "phc"
    court_name: str = "Peshawar High Court"
    source_url: str = "https://peshawarhighcourt.gov.pk"
    schedule: str = "0 3 * * 4"
    priority: str = "P1"

    BENCHES: list[str] = [
        "Peshawar",
        "Abbottabad",
        "Mingora",
        "D.I. Khan",
    ]

    async def _fetch_search_page(
        self,
        year: int,
        section: str,
        page: int = 1,
    ) -> str:
        """Fetch a page of search results from the PHC judgment portal.

        Args:
            year: Year to search.
            section: PPC section number.
            page: Pagination page number.

        Returns:
            Raw HTML text of the results page.
        """
        form_data: dict[str, Any] = {
            "year": str(year),
            "section": section,
            "case_type": "Criminal",
            "page": str(page),
        }
        response = await self.fetch(
            PHC_JUDGMENT_URL,
            method="POST",
            data=form_data,
        )
        return response.text

    def _parse_results_table(self, html: str) -> list[dict[str, Any]]:
        """Parse PHC judgment search results HTML.

        Handles both table-based and list-based result layouts.

        Args:
            html: Raw HTML of the results page.

        Returns:
            List of case reference dicts.
        """
        soup = BeautifulSoup(html, "html.parser")
        cases: list[dict[str, Any]] = []

        # Try table layout first
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
                    href = link_tag["href"]
                    pdf_url = urljoin(PHC_JUDGMENT_URL, href)

                case_number = cells[0].get_text(strip=True)
                parties = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                date_decided = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                result = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                bench = cells[4].get_text(strip=True) if len(cells) > 4 else ""

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
                    "parties": parties,
                    "title": parties,
                    "date_decided": date_decided,
                    "result": result,
                    "bench": bench,
                    "pdf_url": pdf_url,
                    "court": self.court_name,
                })
            return cases

        # Fallback: card / list layout
        items = soup.find_all("div", class_="judgment") or soup.find_all(
            "div", class_="card"
        ) or soup.find_all("li", class_="list-group-item")
        for item in items:
            text = item.get_text(" ", strip=True)
            link = item.find("a", href=True)
            pdf_url = ""
            if link:
                pdf_url = urljoin(PHC_JUDGMENT_URL, link["href"])

            cn_match = re.search(r"([\w\s.-]+\d+/\d{4})", text)
            case_number = cn_match.group(1).strip() if cn_match else ""

            date_match = re.search(r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})", text)
            date_decided = date_match.group(1) if date_match else ""

            year_val = ""
            if "/" in case_number:
                parts = case_number.split("/")
                year_val = parts[-1].strip()

            cases.append({
                "case_number": case_number,
                "year": year_val,
                "parties": text[:200],
                "title": text[:200],
                "description": text,
                "date_decided": date_decided,
                "pdf_url": pdf_url,
                "court": self.court_name,
            })

        return cases

    def _has_next_page(self, html: str) -> bool:
        """Check if pagination indicates more result pages.

        Args:
            html: HTML response text.

        Returns:
            True if a next-page link exists.
        """
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.find("a", string=lambda t: t and "next" in t.lower())
        if next_link:
            return True
        next_li = soup.find("li", class_="next")
        if next_li and next_li.find("a"):
            return True
        if soup.find("a", attrs={"rel": "next"}):
            return True
        return False

    async def search_cases(
        self, year: int, case_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Search PHC portal for cases by year and type.

        Searches across all PPC sections of interest and handles
        pagination for each section.

        Args:
            year: Year to search.
            case_type: Optional case type filter.

        Returns:
            List of case reference dicts from search results.
        """
        all_cases: list[dict[str, Any]] = []

        for section in PPC_SECTIONS_OF_INTEREST:
            page = 1
            max_pages = 30
            try:
                while page <= max_pages:
                    html = await self._fetch_search_page(year, section, page)
                    page_cases = self._parse_results_table(html)
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
        """Download PHC judgment PDF.

        Delegates to the base class download_judgment which
        fetches from the pdf_url in the case reference.

        Args:
            case_ref: Case reference with download URL.

        Returns:
            Raw PDF bytes or None.
        """
        return await super().download_judgment(case_ref)

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the PHC scraping pipeline.

        Returns:
            List of case records with metadata.
        """
        logger.info("[%s] Starting PHC scrape", self.name)
        results = await self.scrape_year_range()
        logger.info("[%s] PHC scrape complete: %d records", self.name, len(results))
        return results

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a PHC case record.

        Args:
            record: A case record dictionary.

        Returns:
            True if required fields are present.
        """
        required_fields = ["case_number", "year", "court"]
        return all(record.get(f) for f in required_fields)
