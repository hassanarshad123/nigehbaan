"""NCRC State of Children portal scraper.

Scrapes the National Commission on the Rights of the Child (NCRC)
portal at stateofchildren.com for child protection datasets.
This is noted as the "easiest government source to scrape" due to
clean HTML tables with well-structured data.

URL: https://stateofchildren.com/children-dataset/
Schedule: Monthly (0 3 15 * *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class StateOfChildrenScraper(BaseScraper):
    """Scraper for NCRC State of Children portal.

    The NCRC portal presents child protection data in clean HTML
    tables that are straightforward to parse.
    """

    name: str = "stateofchildren"
    source_url: str = "https://stateofchildren.com/children-dataset/"
    schedule: str = "0 3 15 * *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    async def fetch_page(self) -> str:
        """Fetch the children-dataset HTML page."""
        response = await self.fetch(self.source_url)
        return response.text

    def parse_tables(self, html: str) -> list[dict[str, Any]]:
        """Parse all HTML tables from the page into structured data."""
        soup = BeautifulSoup(html, "lxml")
        records: list[dict[str, Any]] = []

        for table in soup.find_all("table"):
            headers: list[str] = []
            header_row = table.find("thead")
            if header_row:
                headers = [
                    th.get_text(strip=True) for th in header_row.find_all("th")
                ]
            else:
                first_row = table.find("tr")
                if first_row:
                    headers = [
                        cell.get_text(strip=True)
                        for cell in first_row.find_all(["th", "td"])
                    ]

            if not headers:
                continue

            body = table.find("tbody") or table
            for row in body.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if not cells or len(cells) < len(headers):
                    continue
                record = dict(zip(headers, cells))
                records.append(record)

        return records

    def normalize_record(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a raw table record into standard schema."""
        normalized: dict[str, Any] = {}
        for key, value in raw.items():
            clean_key = key.strip().lower().replace(" ", "_").replace(".", "")
            if value and value.replace(",", "").replace(".", "").isdigit():
                try:
                    normalized[clean_key] = int(value.replace(",", ""))
                except ValueError:
                    try:
                        normalized[clean_key] = float(value.replace(",", ""))
                    except ValueError:
                        normalized[clean_key] = value
            else:
                normalized[clean_key] = value

        province_map = {
            "kp": "Khyber Pakhtunkhwa",
            "kpk": "Khyber Pakhtunkhwa",
            "ajk": "Azad Jammu & Kashmir",
            "ict": "Islamabad Capital Territory",
            "gb": "Gilgit-Baltistan",
        }
        for field in ["province", "region"]:
            if field in normalized:
                val = str(normalized[field]).strip()
                normalized[field] = province_map.get(val.lower(), val)

        normalized["source"] = self.name
        normalized["scraped_at"] = datetime.now(timezone.utc).isoformat()
        return normalized

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the NCRC scraping pipeline."""
        html = await self.fetch_page()
        raw_records = self.parse_tables(html)
        return [self.normalize_record(r) for r in raw_records]

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a State of Children record."""
        has_data = any(
            isinstance(v, (int, float)) for v in record.values()
        )
        has_category = any(
            k in record
            for k in ["province", "region", "category", "indicator"]
        )
        return has_data or has_category
