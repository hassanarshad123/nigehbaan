"""UNODC (United Nations Office on Drugs and Crime) data scraper.

URL: https://dataunodc.un.org
Schedule: Quarterly (0 3 1 */3 *)
Priority: P2
"""

from datetime import datetime, timezone
from pathlib import Path
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

    COUNTRY_CODE: str = "PAK"

    # UNODC data portal API endpoints for trafficking data
    DATA_ENDPOINTS: dict[str, str] = {
        "victims_detected": "/api/data/TIP/victims_detected",
        "criminal_justice": "/api/data/TIP/criminal_justice",
        "trafficking_flows": "/api/data/TIP/trafficking_flows",
    }

    # GLO.ACT report search terms
    GLOACT_SEARCH: str = "GLO.ACT Pakistan"

    async def fetch_portal_data(
        self, indicator: str
    ) -> list[dict[str, Any]]:
        """Query UNODC data portal for a specific indicator."""
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
            logger.warning("[%s] Error fetching %s: %s", self.name, indicator, exc)

        return records

    async def download_csv_export(self, dataset_id: str) -> str | None:
        """Download CSV export from UNODC data portal."""
        url = f"{self.source_url}/api/data/export/{dataset_id}?format=csv&country={self.COUNTRY_CODE}"
        try:
            response = await self.fetch(url)
            csv_content = response.text
            if csv_content and len(csv_content) > 100:
                # Save to raw directory
                raw_dir = self.get_raw_dir()
                csv_path = raw_dir / f"{dataset_id}_{self.run_id}.csv"
                csv_path.write_text(csv_content, encoding="utf-8")
                logger.info("[%s] Saved CSV: %s", self.name, csv_path)
                return csv_content
        except Exception as exc:
            logger.warning("[%s] Error downloading CSV for %s: %s", self.name, dataset_id, exc)
        return None

    async def download_gloact_reports(self) -> list[dict[str, Any]]:
        """Download GLO.ACT programme reports."""
        reports: list[dict[str, Any]] = []
        try:
            # Search UNODC publications page
            response = await self.fetch(
                "https://www.unodc.org/unodc/en/human-trafficking/glo-act/publications.html"
            )
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
            logger.warning("[%s] Error fetching GLO.ACT reports: %s", self.name, exc)

        return reports

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the UNODC scraping pipeline."""
        all_records: list[dict[str, Any]] = []

        # Fetch portal data for each indicator
        for indicator in self.DATA_ENDPOINTS:
            records = await self.fetch_portal_data(indicator)
            all_records.extend(records)

        # Try CSV exports
        for dataset_id in ["TIP", "trafficking"]:
            await self.download_csv_export(dataset_id)

        # Download GLO.ACT reports
        gloact = await self.download_gloact_reports()
        all_records.extend(gloact)

        logger.info("[%s] Collected %d records total", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a UNODC data record."""
        return bool(record.get("indicator") or record.get("pdf_url"))
