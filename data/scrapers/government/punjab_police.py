"""Punjab Police portal scraper.

Scrapes punjabpolice.gov.pk for missing persons lists and crime statistics.

URLs:
    - Missing persons: https://punjabpolice.gov.pk/missing-persons
    - Crime stats: https://punjabpolice.gov.pk/crimestatistics

Schedule: Monthly (0 3 1 * *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class PunjabPoliceScraper(BaseScraper):
    """Scraper for Punjab Police missing persons and crime statistics."""

    name: str = "punjab_police"
    source_url: str = "https://punjabpolice.gov.pk"
    missing_url: str = "https://punjabpolice.gov.pk/missing-persons"
    crime_stats_url: str = "https://punjabpolice.gov.pk/crimestatistics"
    schedule: str = "0 3 1 * *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    async def fetch_missing_persons(self) -> list[dict[str, Any]]:
        """Fetch and parse the quarterly missing persons list."""
        records: list[dict[str, Any]] = []
        try:
            response = await self.fetch(self.missing_url)
            soup = BeautifulSoup(response.text, "lxml")

            tables = soup.find_all("table")
            for table in tables:
                headers: list[str] = []
                header_row = table.find("tr")
                if header_row:
                    headers = [
                        cell.get_text(strip=True)
                        for cell in header_row.find_all(["th", "td"])
                    ]

                for row in table.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if not cells or len(cells) < 2:
                        continue
                    record = dict(zip(headers, cells)) if headers else {
                        f"col_{i}": c for i, c in enumerate(cells)
                    }
                    record["record_type"] = "missing_person"
                    record["source"] = self.name
                    record["scraped_at"] = datetime.now(timezone.utc).isoformat()
                    records.append(record)

            # Check for PDF/CSV download links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if any(ext in href.lower() for ext in [".pdf", ".csv", ".xlsx"]):
                    if "missing" in href.lower() or "missing" in link.get_text(strip=True).lower():
                        records.append({
                            "record_type": "missing_persons_file",
                            "file_url": href if href.startswith("http") else f"{self.source_url}{href}",
                            "title": link.get_text(strip=True),
                            "source": self.name,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                        })

        except Exception as exc:
            logger.error("[%s] Error fetching missing persons: %s", self.name, exc)
        return records

    async def fetch_crime_statistics(self) -> list[dict[str, Any]]:
        """Fetch and parse crime statistics data."""
        records: list[dict[str, Any]] = []
        try:
            response = await self.fetch(self.crime_stats_url)
            soup = BeautifulSoup(response.text, "lxml")

            relevant_categories = {
                "kidnapping", "abduction", "trafficking", "missing",
                "rape", "child", "minor", "zina", "sexual",
            }

            for table in soup.find_all("table"):
                headers: list[str] = []
                for th in table.find_all("th"):
                    headers.append(th.get_text(strip=True))

                if not headers:
                    first_row = table.find("tr")
                    if first_row:
                        headers = [
                            c.get_text(strip=True)
                            for c in first_row.find_all(["th", "td"])
                        ]

                for row in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if not cells or len(cells) < 2:
                        continue

                    row_text = " ".join(cells).lower()
                    is_relevant = any(cat in row_text for cat in relevant_categories)

                    record = dict(zip(headers, cells)) if headers else {
                        f"col_{i}": c for i, c in enumerate(cells)
                    }
                    record["record_type"] = "crime_statistic"
                    record["is_relevant"] = is_relevant
                    record["province"] = "Punjab"
                    record["source"] = self.name
                    record["scraped_at"] = datetime.now(timezone.utc).isoformat()
                    records.append(record)

        except Exception as exc:
            logger.error("[%s] Error fetching crime stats: %s", self.name, exc)
        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the Punjab Police scraping pipeline."""
        missing = await self.fetch_missing_persons()
        crime_stats = await self.fetch_crime_statistics()
        return missing + crime_stats

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Punjab Police record."""
        return bool(record.get("record_type"))
