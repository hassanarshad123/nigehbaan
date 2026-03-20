"""World Bank API scraper for Pakistan development indicators.

API: https://api.worldbank.org/v2/country/PAK/indicator/{indicator_code}
Schedule: Quarterly (0 3 1 */3 *)
Priority: P2
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

import logging

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# World Bank indicator codes relevant to trafficking vulnerability
INDICATORS: dict[str, str] = {
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "SI.POV.NAHC": "Poverty headcount ratio at national poverty lines",
    "SI.POV.DDAY": "Poverty headcount ratio at $2.15/day",
    "SE.PRM.ENRR": "School enrollment, primary (% gross)",
    "SE.SEC.ENRR": "School enrollment, secondary (% gross)",
    "SE.PRM.CMPT.ZS": "Primary completion rate (% of relevant age group)",
    "SE.ADT.LITR.ZS": "Literacy rate, adult total",
    "SE.ADT.LITR.FE.ZS": "Literacy rate, adult female",
    "SP.POP.TOTL": "Population, total",
    "SP.POP.0014.TO.ZS": "Population ages 0-14 (% of total)",
    "SL.TLF.0714.WK.ZS": "Children in employment, ages 7-14 (%)",
    "SP.DYN.IMRT.IN": "Infant mortality rate",
    "SH.STA.BRTC.ZS": "Births attended by skilled health staff (%)",
    "SP.URB.TOTL.IN.ZS": "Urban population (% of total)",
}


class WorldBankAPIScraper(BaseScraper):
    """Scraper for World Bank development indicators via REST API."""

    name: str = "worldbank_api"
    source_url: str = "https://api.worldbank.org/v2/country/PAK/indicator/"
    schedule: str = "0 3 1 */3 *"
    priority: str = "P2"
    rate_limit_delay: float = 0.5  # World Bank API is generous

    API_BASE: str = "https://api.worldbank.org/v2"
    COUNTRY_CODE: str = "PAK"
    FORMAT: str = "json"

    def build_api_url(
        self, indicator_code: str, per_page: int = 100
    ) -> str:
        """Construct the API URL for a specific indicator."""
        return (
            f"{self.API_BASE}/country/{self.COUNTRY_CODE}"
            f"/indicator/{indicator_code}"
            f"?format={self.FORMAT}&per_page={per_page}"
        )

    async def fetch_indicator(
        self, indicator_code: str
    ) -> list[dict[str, Any]]:
        """Fetch time-series data for a single indicator."""
        url = self.build_api_url(indicator_code)
        try:
            response = await self.fetch(url)
            data = response.json()

            if not isinstance(data, list) or len(data) < 2:
                logger.warning("[%s] Empty response for %s", self.name, indicator_code)
                return []

            records: list[dict[str, Any]] = []
            indicator_desc = INDICATORS.get(indicator_code, indicator_code)

            for entry in data[1] or []:
                if entry.get("value") is not None:
                    records.append({
                        "indicator_code": indicator_code,
                        "indicator_name": indicator_desc,
                        "year": int(entry["date"]) if entry.get("date") else None,
                        "value": entry["value"],
                        "country": "Pakistan",
                        "source": self.name,
                    })

            return records

        except Exception as exc:
            logger.error("[%s] Error fetching %s: %s", self.name, indicator_code, exc)
            return []

    async def fetch_all_indicators(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch all configured indicators concurrently."""
        tasks = {
            code: self.fetch_indicator(code)
            for code in INDICATORS
        }

        results: dict[str, list[dict[str, Any]]] = {}
        gathered = await asyncio.gather(
            *tasks.values(), return_exceptions=True
        )

        for code, result in zip(tasks.keys(), gathered):
            if isinstance(result, Exception):
                logger.error("[%s] Failed to fetch %s: %s", self.name, code, result)
                results[code] = []
            else:
                results[code] = result

        return results

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the World Bank API scraping pipeline."""
        indicator_data = await self.fetch_all_indicators()

        all_records: list[dict[str, Any]] = []
        for code, records in indicator_data.items():
            all_records.extend(records)
            logger.info(
                "[%s] %s: %d data points",
                self.name, code, len(records),
            )

        # Add scraped_at timestamp
        now = datetime.now(timezone.utc).isoformat()
        for record in all_records:
            record["scraped_at"] = now

        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a World Bank indicator record."""
        return bool(
            record.get("indicator_code")
            and record.get("year")
            and record.get("value") is not None
        )
