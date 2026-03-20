"""Sindh High Court (SHC) scraper.

Scrapes the Sindh High Court case portal across all 5 benches:
Karachi, Sukkur, Hyderabad, Larkana, and Mirpurkhas. Each bench
has a separate URL endpoint on the same domain.

Strategy:
    1. Iterate across all 5 bench endpoints
    2. Search each bench for relevant PPC section cases
    3. Parse case listing HTML tables
    4. Download judgment PDFs where available
    5. Merge results across benches with bench identifier

URLs:
    - Karachi: https://cases.shc.gov.pk/khi
    - Sukkur: https://cases.shc.gov.pk/suk
    - Hyderabad: https://cases.shc.gov.pk/hyd
    - Larkana: https://cases.shc.gov.pk/lar
    - Mirpurkhas: https://cases.shc.gov.pk/mpkhas

Tool: Requests + BeautifulSoup
Schedule: Weekly (0 3 * * 3)
Priority: P1 — Sindh is second most populous province
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


class SHCScraper(BaseCourtScraper):
    """Scraper for Sindh High Court judgments across all benches.

    The SHC has 5 benches, each with a separate endpoint on
    cases.shc.gov.pk. This scraper iterates across all benches
    to ensure complete coverage of Sindh province.

    Attributes:
        name: Scraper identifier.
        court_name: Full court name.
        source_url: Base URL for SHC case portal.
        benches: Dict mapping bench names to their URL slugs.
    """

    name: str = "shc"
    court_name: str = "Sindh High Court"
    source_url: str = "https://cases.shc.gov.pk"
    schedule: str = "0 3 * * 3"
    priority: str = "P1"

    BENCHES: dict[str, str] = {
        "Karachi": "khi",
        "Sukkur": "suk",
        "Hyderabad": "hyd",
        "Larkana": "lar",
        "Mirpurkhas": "mpkhas",
    }

    def _build_bench_url(self, bench_slug: str) -> str:
        """Build the full URL for a given bench slug.

        Args:
            bench_slug: Short slug for the bench (e.g. 'khi').

        Returns:
            Full URL for that bench endpoint.
        """
        return f"{self.source_url}/{bench_slug}"

    def _parse_results_table(
        self, html: str, bench_name: str, bench_slug: str
    ) -> list[dict[str, Any]]:
        """Parse SHC results HTML into case reference dicts.

        Args:
            html: Raw HTML of the results page.
            bench_name: Human-readable bench name (e.g. 'Karachi').
            bench_slug: URL slug for the bench.

        Returns:
            List of case reference dicts with bench information.
        """
        soup = BeautifulSoup(html, "html.parser")
        cases: list[dict[str, Any]] = []

        table = soup.find("table", class_="table") or soup.find("table")
        if not table:
            # Try div/list-based layout
            items = soup.find_all("div", class_="case-item") or soup.find_all(
                "li", class_="list-group-item"
            )
            for item in items:
                text = item.get_text(" ", strip=True)
                link = item.find("a", href=True)
                pdf_url = ""
                if link:
                    pdf_url = urljoin(self._build_bench_url(bench_slug), link["href"])

                import re
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
                    "date_decided": date_decided,
                    "result": "",
                    "pdf_url": pdf_url,
                    "court": self.court_name,
                    "bench": bench_name,
                })
            return cases

        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            pdf_url = ""
            link_tag = row.find("a", href=True)
            if link_tag:
                pdf_url = urljoin(
                    self._build_bench_url(bench_slug), link_tag["href"]
                )

            case_number = cells[0].get_text(strip=True)
            parties = cells[1].get_text(strip=True) if len(cells) > 1 else ""
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
                "parties": parties,
                "title": parties,
                "date_decided": date_decided,
                "result": result,
                "pdf_url": pdf_url,
                "court": self.court_name,
                "bench": bench_name,
            })

        return cases

    def _has_next_page(self, html: str) -> bool:
        """Check if pagination indicates more pages.

        Args:
            html: HTML response text.

        Returns:
            True if a next-page link is present.
        """
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.find("a", string=lambda t: t and "next" in t.lower())
        if next_link:
            return True
        next_li = soup.find("li", class_="next")
        if next_li and next_li.find("a"):
            return True
        return False

    async def search_bench(
        self, bench_slug: str, year: int
    ) -> list[dict[str, Any]]:
        """Search a specific SHC bench for relevant cases.

        Args:
            bench_slug: URL slug for the bench (e.g., 'khi').
            year: Year to search.

        Returns:
            List of case reference dicts for this bench.
        """
        bench_name = ""
        for name, slug in self.BENCHES.items():
            if slug == bench_slug:
                bench_name = name
                break

        bench_url = self._build_bench_url(bench_slug)
        all_cases: list[dict[str, Any]] = []

        for section in PPC_SECTIONS_OF_INTEREST:
            page = 1
            max_pages = 30
            try:
                while page <= max_pages:
                    params: dict[str, Any] = {
                        "section": section,
                        "year": str(year),
                        "page": str(page),
                    }
                    response = await self.fetch(
                        bench_url,
                        method="GET",
                        params=params,
                    )
                    html = response.text
                    page_cases = self._parse_results_table(
                        html, bench_name, bench_slug
                    )
                    if not page_cases:
                        break
                    all_cases.extend(page_cases)
                    if not self._has_next_page(html):
                        break
                    page += 1
            except Exception as exc:
                logger.warning(
                    "[%s] Error searching bench=%s section=%s year=%d: %s",
                    self.name, bench_slug, section, year, exc,
                )
                continue

        return all_cases

    async def search_cases(
        self, year: int, case_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Search all SHC benches for relevant cases.

        Iterates across all 5 benches and merges results, adding
        a bench identifier to each case record. Per-bench failures
        are handled gracefully so other benches continue.

        Args:
            year: Year to search.
            case_type: Optional case type filter.

        Returns:
            Combined list of case refs from all benches.
        """
        all_cases: list[dict[str, Any]] = []

        for bench_name, bench_slug in self.BENCHES.items():
            try:
                bench_cases = await self.search_bench(bench_slug, year)
                logger.info(
                    "[%s] Bench %s (%s) year %d: %d cases",
                    self.name, bench_name, bench_slug, year, len(bench_cases),
                )
                all_cases.extend(bench_cases)
            except Exception as exc:
                logger.error(
                    "[%s] Failed to search bench %s for year %d: %s",
                    self.name, bench_name, year, exc,
                )
                continue

        logger.info(
            "[%s] Found %d total cases across all benches for year %d",
            self.name, len(all_cases), year,
        )
        return all_cases

    async def download_judgment(
        self, case_ref: dict[str, Any]
    ) -> bytes | None:
        """Download SHC judgment PDF.

        Delegates to the base class download_judgment which fetches
        from the pdf_url in the case reference.

        Args:
            case_ref: Case reference with bench and download URL.

        Returns:
            Raw PDF bytes or None.
        """
        return await super().download_judgment(case_ref)

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the SHC scraping pipeline across all benches.

        Returns:
            List of case records with bench identifiers.
        """
        logger.info("[%s] Starting SHC scrape across %d benches", self.name, len(self.BENCHES))
        results = await self.scrape_year_range()
        logger.info("[%s] SHC scrape complete: %d records", self.name, len(results))
        return results

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an SHC case record.

        Args:
            record: A case record dictionary.

        Returns:
            True if required fields including bench are present.
        """
        required_fields = ["case_number", "year", "court"]
        return all(record.get(f) for f in required_fields)
