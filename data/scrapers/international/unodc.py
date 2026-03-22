"""UNODC (United Nations Office on Drugs and Crime) data scraper.

URL: https://dataunodc.un.org
Schedule: Quarterly (0 3 1 */3 *)
Priority: P2

Updated 2026-03-22: Migrated from old /api/data/TIP/* endpoints to the
current UNODC data portal API at dataunodc.un.org/api/ and the
trafficking-persons data page at dp-trafficking-persons.  Adds a
Wayback Machine fallback if the live portal is unreachable.
"""

from datetime import datetime, timezone
from typing import Any

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class UNODCScraper(BaseScraper):
    """Scraper for UNODC data portal and GLO.ACT reports."""

    name: str = "unodc"
    source_url: str = "https://dataunodc.un.org"
    schedule: str = "0 3 1 */3 *"
    priority: str = "P2"
    rate_limit_delay: float = 1.0
    request_timeout: float = 60.0

    COUNTRY_CODE: str = "PAK"

    # Current UNODC data portal API endpoints (2026 structure)
    DATA_API_BASE: str = "https://dataunodc.un.org/api"
    DATA_ENDPOINTS: dict[str, str] = {
        "victims_detected": "/1/trafficking-persons/victims-detected",
        "criminal_justice": "/1/trafficking-persons/criminal-justice",
        "trafficking_flows": "/1/trafficking-persons/trafficking-flows",
    }

    # Fallback endpoint patterns — UNODC has restructured multiple times
    LEGACY_ENDPOINTS: dict[str, list[str]] = {
        "victims_detected": [
            "/api/data/TIP/victims_detected",
            "/api/data/trafficking-persons/victims-detected",
        ],
        "criminal_justice": [
            "/api/data/TIP/criminal_justice",
            "/api/data/trafficking-persons/criminal-justice",
        ],
        "trafficking_flows": [
            "/api/data/TIP/trafficking_flows",
            "/api/data/trafficking-persons/trafficking-flows",
        ],
    }

    # HTML data page — the current trafficking persons data page
    HTML_DATA_URL: str = "https://dataunodc.un.org/dp-trafficking-persons"
    LEGACY_HTML_URL: str = "https://dataunodc.un.org/dp-crime-trafficking-persons"

    # Wayback Machine prefix for fallback
    WAYBACK_PREFIX: str = "https://web.archive.org/web/2024"

    # GLO.ACT report search terms
    GLOACT_SEARCH: str = "GLO.ACT Pakistan"

    async def _try_api_url(
        self, url: str, params: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        """Try a single API URL and return parsed items or None on failure."""
        try:
            response = await self.fetch(url, params=params)
            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("data", data.get("items", data.get("results", [])))
        except Exception as exc:
            logger.debug("[%s] API URL failed %s: %s", self.name, url, exc)
        return None

    async def fetch_portal_data(
        self, indicator: str
    ) -> list[dict[str, Any]]:
        """Query UNODC data portal for a specific indicator.

        Tries the current API endpoint first, then legacy endpoints,
        then the HTML data page, then the Wayback Machine as a last resort.
        """
        records: list[dict[str, Any]] = []
        params = {"country": self.COUNTRY_CODE, "format": "json"}

        # Strategy 1: Current API endpoint
        current_path = self.DATA_ENDPOINTS.get(indicator)
        if current_path:
            url = f"{self.DATA_API_BASE}{current_path}"
            items = await self._try_api_url(url, params)
            if items:
                records.extend(self._parse_api_items(items, indicator))
                return records

        # Strategy 2: Legacy API endpoints
        for legacy_path in self.LEGACY_ENDPOINTS.get(indicator, []):
            url = f"{self.source_url}{legacy_path}"
            items = await self._try_api_url(url, params)
            if items:
                records.extend(self._parse_api_items(items, indicator))
                return records

        # Strategy 3: HTML data page scraping
        logger.info(
            "[%s] API endpoints failed for %s — trying HTML scraping",
            self.name, indicator,
        )
        try:
            html_records = await self._scrape_html_data(indicator)
            if html_records:
                return html_records
        except Exception as exc:
            logger.warning(
                "[%s] HTML scraping failed for %s: %s",
                self.name, indicator, exc,
            )

        # Strategy 4: Wayback Machine fallback
        logger.info(
            "[%s] Live sources failed for %s — trying Wayback Machine",
            self.name, indicator,
        )
        try:
            wayback_records = await self._scrape_wayback(indicator)
            if wayback_records:
                return wayback_records
        except Exception as exc:
            logger.warning(
                "[%s] Wayback fallback also failed for %s: %s",
                self.name, indicator, exc,
            )

        logger.warning(
            "[%s] All strategies exhausted for indicator %s — returning empty",
            self.name, indicator,
        )
        return records

    def _parse_api_items(
        self, items: list[dict[str, Any]], indicator: str
    ) -> list[dict[str, Any]]:
        """Parse API response items into standardized statistical_reports records."""
        records: list[dict[str, Any]] = []
        scraped_at = datetime.now(timezone.utc).isoformat()

        for item in items:
            # UNODC API uses various key casings across versions
            year = (
                item.get("year")
                or item.get("Year")
                or item.get("TimePeriod")
                or item.get("time_period")
            )
            value = (
                item.get("value")
                or item.get("Value")
                or item.get("Measure")
                or item.get("measure")
            )
            category = (
                item.get("category")
                or item.get("Category")
                or item.get("Dimension")
                or item.get("dimension")
            )
            country = (
                item.get("country")
                or item.get("Country")
                or item.get("Geo")
                or "Pakistan"
            )

            records.append({
                "source_name": "UNODC",
                "report_title": f"UNODC {indicator.replace('_', ' ').title()}",
                "indicator": indicator,
                "year": year,
                "value": value,
                "country": country,
                "category": category,
                "source": self.name,
                "source_url": self.source_url,
                "scraped_at": scraped_at,
            })

        return records

    async def _scrape_html_data(self, indicator: str) -> list[dict[str, Any]]:
        """Fallback: scrape trafficking data from the UNODC HTML data page."""
        records: list[dict[str, Any]] = []

        # Try current URL first, then legacy
        for page_url in [self.HTML_DATA_URL, self.LEGACY_HTML_URL]:
            try:
                response = await self.fetch(page_url)
                soup = BeautifulSoup(response.text, "lxml")
                page_records = self._extract_table_records(soup, indicator)
                if page_records:
                    records.extend(page_records)
                    logger.info(
                        "[%s] HTML scrape found %d records from %s",
                        self.name, len(page_records), page_url,
                    )
                    return records
            except Exception as exc:
                logger.debug(
                    "[%s] HTML page %s failed: %s", self.name, page_url, exc
                )

        return records

    async def _scrape_wayback(self, indicator: str) -> list[dict[str, Any]]:
        """Last-resort fallback: fetch from the Wayback Machine."""
        records: list[dict[str, Any]] = []

        # Try Wayback snapshots of both the API and HTML pages
        wayback_urls = [
            f"{self.WAYBACK_PREFIX}/{self.HTML_DATA_URL}",
            f"{self.WAYBACK_PREFIX}/{self.LEGACY_HTML_URL}",
        ]

        for wb_url in wayback_urls:
            try:
                response = await self.fetch(wb_url)
                soup = BeautifulSoup(response.text, "lxml")
                page_records = self._extract_table_records(soup, indicator)
                if page_records:
                    # Mark records as coming from archive
                    for rec in page_records:
                        rec["archive_source"] = "wayback_machine"
                    records.extend(page_records)
                    logger.info(
                        "[%s] Wayback found %d records from %s",
                        self.name, len(page_records), wb_url,
                    )
                    return records
            except Exception as exc:
                logger.debug(
                    "[%s] Wayback URL %s failed: %s", self.name, wb_url, exc
                )

        return records

    def _extract_table_records(
        self, soup: BeautifulSoup, indicator: str
    ) -> list[dict[str, Any]]:
        """Extract Pakistan-related records from HTML tables."""
        records: list[dict[str, Any]] = []
        scraped_at = datetime.now(timezone.utc).isoformat()

        for table in soup.find_all("table"):
            headers = [
                th.get_text(strip=True).lower() for th in table.find_all("th")
            ]
            if not headers:
                continue
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if not cells or len(cells) < 2:
                    continue
                row_text = " ".join(cells).lower()
                if "pakistan" in row_text or "pak" in row_text:
                    row_dict = dict(zip(headers, cells))
                    records.append({
                        "source_name": "UNODC",
                        "report_title": f"UNODC {indicator.replace('_', ' ').title()}",
                        "indicator": indicator,
                        "country": "Pakistan",
                        "year": row_dict.get("year", row_dict.get("time period", "")),
                        "value": row_dict.get("value", row_dict.get("count", "")),
                        "category": row_dict.get("category", row_dict.get("dimension", "")),
                        "source": self.name,
                        "source_url": self.source_url,
                        "scraped_at": scraped_at,
                        **{k: v for k, v in row_dict.items() if k not in ("year", "value", "category")},
                    })

        return records

    async def download_csv_export(self, dataset_id: str) -> str | None:
        """Download CSV export from UNODC data portal.

        Tries multiple URL patterns since UNODC has restructured several times.
        """
        url_patterns = [
            # Current API structure
            f"{self.DATA_API_BASE}/1/trafficking-persons/{dataset_id}/export?format=csv&country={self.COUNTRY_CODE}",
            f"{self.DATA_API_BASE}/data/export/{dataset_id}?format=csv&country={self.COUNTRY_CODE}",
            # Legacy patterns
            f"{self.source_url}/api/data/export/{dataset_id}?format=csv&country={self.COUNTRY_CODE}",
            f"{self.source_url}/api/data/{dataset_id}/export?format=csv&country={self.COUNTRY_CODE}",
        ]
        for url in url_patterns:
            try:
                response = await self.fetch(url)
                csv_content = response.text
                if csv_content and len(csv_content) > 100:
                    raw_dir = self.get_raw_dir()
                    csv_path = raw_dir / f"{dataset_id}_{self.run_id}.csv"
                    csv_path.write_text(csv_content, encoding="utf-8")
                    logger.info("[%s] Saved CSV: %s", self.name, csv_path)
                    return csv_content
            except Exception as exc:
                logger.debug("[%s] CSV download failed at %s: %s", self.name, url, exc)
        return None

    async def download_gloact_reports(self) -> list[dict[str, Any]]:
        """Download GLO.ACT programme reports."""
        reports: list[dict[str, Any]] = []
        scraped_at = datetime.now(timezone.utc).isoformat()

        # Search pages to try — GLO.ACT publications + COPAK fallback
        search_pages: list[str] = [
            "https://www.unodc.org/unodc/en/human-trafficking/glo-act/publications.html",
            "https://www.unodc.org/pakistan/en/copak.html",
            # GLO.ACT II page (newer programme)
            "https://www.unodc.org/unodc/en/human-trafficking/glo-act-ii/publications.html",
        ]

        for page_url in search_pages:
            try:
                response = await self.fetch(page_url)
                soup = BeautifulSoup(response.text, "lxml")

                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    text = link.get_text(strip=True)

                    if "pakistan" in text.lower() or "pakistan" in href.lower():
                        full_url = (
                            href
                            if href.startswith("http")
                            else f"https://www.unodc.org{href}"
                        )
                        reports.append({
                            "source_name": "UNODC",
                            "report_title": text or "GLO.ACT Report",
                            "indicator": "gloact_report",
                            "pdf_url": full_url,
                            "is_pdf": href.lower().endswith(".pdf"),
                            "source": self.name,
                            "source_url": page_url,
                            "scraped_at": scraped_at,
                        })
            except Exception as exc:
                logger.warning(
                    "[%s] Error fetching reports from %s: %s",
                    self.name, page_url, exc,
                )

        return reports

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the UNODC scraping pipeline.

        Gracefully returns whatever data it can find — does not fail
        if some endpoints are unreachable.
        """
        all_records: list[dict[str, Any]] = []

        # Fetch portal data for each indicator
        for indicator in self.DATA_ENDPOINTS:
            try:
                records = await self.fetch_portal_data(indicator)
                all_records.extend(records)
            except Exception as exc:
                logger.warning(
                    "[%s] Skipping indicator %s: %s", self.name, indicator, exc
                )

        # Try CSV exports
        for dataset_id in ["TIP", "trafficking", "trafficking-persons"]:
            try:
                await self.download_csv_export(dataset_id)
            except Exception as exc:
                logger.warning(
                    "[%s] CSV export %s failed: %s", self.name, dataset_id, exc
                )

        # Download GLO.ACT reports
        try:
            gloact = await self.download_gloact_reports()
            all_records.extend(gloact)
        except Exception as exc:
            logger.warning("[%s] GLO.ACT reports failed: %s", self.name, exc)

        logger.info("[%s] Collected %d records total", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a UNODC data record."""
        return bool(
            record.get("indicator") or record.get("pdf_url") or record.get("report_title")
        )
