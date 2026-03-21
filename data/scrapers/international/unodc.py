"""UNODC (United Nations Office on Drugs and Crime) data scraper.

URL: https://dataunodc.un.org
Schedule: Quarterly (0 3 1 */3 *)
Priority: P2
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

    # UNODC data portal API endpoints for trafficking data
    DATA_ENDPOINTS: dict[str, str] = {
        "victims_detected": "/api/data/TIP/victims_detected",
        "criminal_justice": "/api/data/TIP/criminal_justice",
        "trafficking_flows": "/api/data/TIP/trafficking_flows",
    }

    # GLO.ACT report search terms
    GLOACT_SEARCH: str = "GLO.ACT Pakistan"

    # Alternative HTML data page if API fails
    HTML_DATA_URL: str = "https://dataunodc.un.org/dp-crime-trafficking-persons"

    async def fetch_portal_data(
        self, indicator: str
    ) -> list[dict[str, Any]]:
        """Query UNODC data portal for a specific indicator.

        Falls back to scraping the HTML data page if the API returns errors.
        """
        records: list[dict[str, Any]] = []
        endpoint = self.DATA_ENDPOINTS.get(indicator)
        if not endpoint:
            logger.warning("[%s] Unknown indicator: %s", self.name, indicator)
            return records

        url = f"{self.source_url}{endpoint}"
        try:
            response = await self.fetch(
                url,
                params={"country": self.COUNTRY_CODE, "format": "json"},
            )
            data = response.json()

            items = data if isinstance(data, list) else data.get("data", data.get("items", []))
            for item in items:
                records.append({
                    "indicator": indicator,
                    "year": item.get("year") or item.get("Year"),
                    "value": item.get("value") or item.get("Value"),
                    "country": "Pakistan",
                    "category": item.get("category") or item.get("Category"),
                    "source": self.name,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })

        except Exception as exc:
            logger.warning("[%s] API error for %s: %s — trying HTML fallback", self.name, indicator, exc)
            try:
                records.extend(await self._scrape_html_data(indicator))
            except Exception as html_exc:
                logger.warning("[%s] HTML fallback also failed for %s: %s", self.name, indicator, html_exc)

        return records

    async def _scrape_html_data(self, indicator: str) -> list[dict[str, Any]]:
        """Fallback: scrape trafficking data from the UNODC HTML data page."""
        records: list[dict[str, Any]] = []
        response = await self.fetch(self.HTML_DATA_URL)
        soup = BeautifulSoup(response.text, "lxml")

        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if not headers:
                continue
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if not cells or len(cells) < 2:
                    continue
                row_text = " ".join(cells).lower()
                if "pakistan" in row_text or "pak" in row_text:
                    record = dict(zip(headers, cells))
                    record["indicator"] = indicator
                    record["country"] = "Pakistan"
                    record["source"] = self.name
                    record["scraped_at"] = datetime.now(timezone.utc).isoformat()
                    records.append(record)

        logger.info("[%s] HTML fallback found %d records for %s", self.name, len(records), indicator)
        return records

    async def download_csv_export(self, dataset_id: str) -> str | None:
        """Download CSV export from UNODC data portal.

        Tries multiple URL patterns since UNODC may have restructured.
        """
        url_patterns = [
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
                logger.warning("[%s] CSV download failed at %s: %s", self.name, url, exc)
        return None

    async def download_gloact_reports(self) -> list[dict[str, Any]]:
        """Download GLO.ACT programme reports."""
        reports: list[dict[str, Any]] = []

        # Search pages to try — GLO.ACT publications + COPAK fallback
        search_pages: list[str] = [
            "https://www.unodc.org/unodc/en/human-trafficking/glo-act/publications.html",
            "https://www.unodc.org/pakistan/en/copak.html",
        ]

        for page_url in search_pages:
            try:
                response = await self.fetch(page_url)
                soup = BeautifulSoup(response.text, "lxml")

                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    text = link.get_text(strip=True)

                    if "pakistan" in text.lower() or "pakistan" in href.lower():
                        full_url = href if href.startswith("http") else f"https://www.unodc.org{href}"
                        reports.append({
                            "title": text,
                            "pdf_url": full_url,
                            "is_pdf": href.lower().endswith(".pdf"),
                            "source": self.name,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                        })
            except Exception as exc:
                logger.warning("[%s] Error fetching reports from %s: %s", self.name, page_url, exc)

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
                logger.warning("[%s] Skipping indicator %s: %s", self.name, indicator, exc)

        # Try CSV exports
        for dataset_id in ["TIP", "trafficking"]:
            try:
                await self.download_csv_export(dataset_id)
            except Exception as exc:
                logger.warning("[%s] CSV export %s failed: %s", self.name, dataset_id, exc)

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
        return bool(record.get("indicator") or record.get("pdf_url"))
