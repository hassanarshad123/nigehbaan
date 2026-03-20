"""UNHCR Refugee Data Finder API scraper.

API: https://api.unhcr.org/population/v1/
Schedule: Quarterly (0 3 15 */3 *)
Priority: P2
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

import logging

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class UNHCRAPIScraper(BaseScraper):
    """Scraper for UNHCR Refugee Data Finder API."""

    name: str = "unhcr_api"
    source_url: str = "https://api.unhcr.org/population/v1/"
    schedule: str = "0 3 15 */3 *"
    priority: str = "P2"
    rate_limit_delay: float = 0.5

    API_BASE: str = "https://api.unhcr.org/population/v1"
    COUNTRY_ASYLUM: str = "PAK"

    async def fetch_population_data(
        self, year: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetch refugee population data for Pakistan."""
        params: dict[str, Any] = {
            "limit": 100,
            "country_asylum": self.COUNTRY_ASYLUM,
            "page": 1,
        }
        if year:
            params["year"] = year

        records: list[dict[str, Any]] = []
        try:
            response = await self.fetch(
                f"{self.API_BASE}/population/",
                params=params,
            )
            data = response.json()

            items = data.get("items", data.get("data", []))
            if isinstance(data, list):
                items = data

            for item in items:
                records.append({
                    "record_type": "population",
                    "year": item.get("year"),
                    "country_origin": item.get("country_origin", {}).get("name", item.get("country_origin", "")),
                    "country_asylum": "Pakistan",
                    "population_type": item.get("population_type", ""),
                    "count": item.get("individuals", item.get("value", 0)),
                    "source": self.name,
                })

        except Exception as exc:
            logger.error("[%s] Error fetching population data: %s", self.name, exc)

        return records

    async def fetch_demographics(
        self, year: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetch demographic breakdown of refugee population."""
        params: dict[str, Any] = {
            "limit": 100,
            "country_asylum": self.COUNTRY_ASYLUM,
        }
        if year:
            params["year"] = year

        records: list[dict[str, Any]] = []
        try:
            response = await self.fetch(
                f"{self.API_BASE}/demographics/",
                params=params,
            )
            data = response.json()

            items = data.get("items", data.get("data", []))
            if isinstance(data, list):
                items = data

            for item in items:
                records.append({
                    "record_type": "demographics",
                    "year": item.get("year"),
                    "country_origin": item.get("country_origin", {}).get("name", item.get("country_origin", "")),
                    "female_total": item.get("female_total", 0),
                    "male_total": item.get("male_total", 0),
                    "female_0_4": item.get("female_0_4", 0),
                    "male_0_4": item.get("male_0_4", 0),
                    "female_5_11": item.get("female_5_11", 0),
                    "male_5_11": item.get("male_5_11", 0),
                    "female_12_17": item.get("female_12_17", 0),
                    "male_12_17": item.get("male_12_17", 0),
                    "source": self.name,
                })

        except Exception as exc:
            logger.error("[%s] Error fetching demographics: %s", self.name, exc)

        return records

    async def fetch_settlement_locations(self) -> list[dict[str, Any]]:
        """Fetch refugee settlement/camp location data."""
        records: list[dict[str, Any]] = []
        try:
            response = await self.fetch(
                f"{self.API_BASE}/solutions/",
                params={
                    "limit": 100,
                    "country_asylum": self.COUNTRY_ASYLUM,
                },
            )
            data = response.json()
            items = data.get("items", data.get("data", []))
            if isinstance(data, list):
                items = data

            for item in items:
                records.append({
                    "record_type": "settlement",
                    "year": item.get("year"),
                    "location": item.get("location", ""),
                    "population": item.get("individuals", 0),
                    "source": self.name,
                })

        except Exception as exc:
            logger.warning("[%s] Error fetching settlements: %s", self.name, exc)

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the UNHCR API scraping pipeline."""
        population_task = self.fetch_population_data()
        demographics_task = self.fetch_demographics()
        settlements_task = self.fetch_settlement_locations()

        results = await asyncio.gather(
            population_task, demographics_task, settlements_task,
            return_exceptions=True,
        )

        all_records: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("[%s] Task failed: %s", self.name, result)
            elif isinstance(result, list):
                all_records.extend(result)

        now = datetime.now(timezone.utc).isoformat()
        for record in all_records:
            record["scraped_at"] = now

        logger.info("[%s] Collected %d records total", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a UNHCR data record."""
        return bool(record.get("record_type"))
