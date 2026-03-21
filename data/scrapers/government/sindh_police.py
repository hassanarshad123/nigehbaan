"""Sindh Police portal scraper.

Scrapes sindhpolice.gov.pk for crime statistics at range level.

URLs:
    - Crime stats: https://sindhpolice.gov.pk/annoucements/crime_stat_all_cities.html
    - Missing persons: https://sindhpolice.gov.pk/missing_person (currently 403)

Schedule: Monthly (0 3 5 * *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SindhPoliceScraper(BaseScraper):
    """Scraper for Sindh Police crime statistics."""

    name: str = "sindh_police"
    source_url: str = "https://sindhpolice.gov.pk"
    missing_url: str = "https://sindhpolice.gov.pk/missing_person"
    schedule: str = "0 3 5 * *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0
    request_timeout: float = 60.0
    max_retries: int = 5
    use_firecrawl: bool = True  # Sindh Police WAF blocks server IPs

    CRIME_STATS_URLS: list[str] = [
        "https://sindhpolice.gov.pk/announcements/crime_stat_all_cities.html",
        "https://sindhpolice.gov.pk/annoucements/crime_stat_all_cities.html",  # old typo URL
        "https://sindhpolice.gov.pk/crime-statistics",
    ]

    async def fetch_crime_statistics(self) -> list[dict[str, Any]]:
        """Fetch and parse range-level crime statistics.

        Tries multiple URLs since the site has had URL typos historically.
        """
        records: list[dict[str, Any]] = []
        response = None
        for url in self.CRIME_STATS_URLS:
            try:
                response = await self.fetch(url)
                if response.status_code == 200:
                    logger.info("[%s] Crime stats fetched from %s", self.name, url)
                    break
            except Exception as exc:
                logger.warning("[%s] Failed to fetch %s: %s", self.name, url, exc)
                continue

        # Wayback Machine fallback if all live URLs failed
        if not response:
            logger.warning("[%s] All live crime stats URLs failed, trying Wayback Machine", self.name)
            for url in self.CRIME_STATS_URLS:
                wayback_url = f"https://web.archive.org/web/2024/{url}"
                try:
                    response = await self.fetch(wayback_url)
                    if response.status_code == 200:
                        logger.info("[%s] Wayback fallback succeeded for %s", self.name, url)
                        break
                except Exception as exc:
                    logger.warning("[%s] Wayback fallback failed for %s: %s", self.name, url, exc)
                    continue

        if not response:
            logger.error("[%s] All crime stats URLs failed (including Wayback)", self.name)
            return records

        try:
            soup = BeautifulSoup(response.text, "lxml")

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

                    record = dict(zip(headers, cells)) if headers and len(headers) >= len(cells) else {
                        f"col_{i}": c for i, c in enumerate(cells)
                    }
                    record["record_type"] = "crime_statistic"
                    record["province"] = "Sindh"
                    record["source"] = self.name
                    record["scraped_at"] = datetime.now(timezone.utc).isoformat()
                    records.append(record)

        except Exception as exc:
            logger.error("[%s] Error fetching crime stats: %s", self.name, exc)
        return records

    async def check_missing_persons(self) -> bool:
        """Check if the missing persons page is accessible."""
        try:
            client = await self.get_client()
            response = await client.head(self.missing_url, follow_redirects=True)
            is_available = response.status_code == 200
            if is_available:
                logger.info("[%s] Missing persons page is now available!", self.name)
            else:
                logger.debug(
                    "[%s] Missing persons page status: %d",
                    self.name, response.status_code,
                )
            return is_available
        except Exception:
            return False

    async def fetch_missing_persons(self) -> list[dict[str, Any]]:
        """Fetch missing persons data if the page is accessible."""
        is_available = await self.check_missing_persons()
        response = None

        if is_available:
            try:
                response = await self.fetch(self.missing_url)
            except Exception as exc:
                logger.warning("[%s] Live missing persons fetch failed: %s", self.name, exc)

        # Wayback Machine fallback
        if not response:
            wayback_url = f"https://web.archive.org/web/2024/{self.missing_url}"
            try:
                response = await self.fetch(wayback_url)
                logger.info("[%s] Wayback fallback succeeded for missing persons", self.name)
            except Exception as exc:
                logger.info("[%s] Missing persons page unavailable (incl. Wayback): %s", self.name, exc)
                return []

        records: list[dict[str, Any]] = []
        try:
            soup = BeautifulSoup(response.text, "lxml")

            for table in soup.find_all("table"):
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                for row in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if not cells:
                        continue
                    record = dict(zip(headers, cells)) if headers else {
                        f"col_{i}": c for i, c in enumerate(cells)
                    }
                    record["record_type"] = "missing_person"
                    record["province"] = "Sindh"
                    record["source"] = self.name
                    record["scraped_at"] = datetime.now(timezone.utc).isoformat()
                    records.append(record)
        except Exception as exc:
            logger.error("[%s] Error parsing missing persons: %s", self.name, exc)
        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the Sindh Police scraping pipeline."""
        crime_stats = await self.fetch_crime_statistics()
        missing = await self.fetch_missing_persons()
        return crime_stats + missing

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Sindh Police record."""
        return bool(record.get("record_type"))
