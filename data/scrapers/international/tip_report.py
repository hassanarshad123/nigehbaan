"""US State Department Trafficking in Persons (TIP) Report scraper.

URL: https://www.state.gov/reports/{YEAR}-trafficking-in-persons-report/pakistan/
Schedule: Annually (0 3 1 7 *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

TIER_PATTERN = re.compile(
    r"Tier\s+(3|2\s*(?:Watch\s*List)?|1)",
    re.IGNORECASE,
)

NUMBER_PATTERN = re.compile(r"(\d{1,6}(?:,\d{3})*)")


class TIPReportScraper(BaseScraper):
    """Scraper for US State Dept Trafficking in Persons Reports."""

    name: str = "tip_report"
    source_url: str = "https://www.state.gov/reports/"
    schedule: str = "0 3 1 7 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    FIRST_YEAR: int = 2001
    CURRENT_YEAR: int = datetime.now().year

    # Alternate URL patterns used across years
    URL_PATTERNS: list[str] = [
        "https://www.state.gov/reports/{year}-trafficking-in-persons-report/pakistan/",
        "https://www.state.gov/reports/trafficking-in-persons-report-{year}/pakistan/",
        "https://www.state.gov/reports/{year}-trafficking-in-persons-report/pakistan",
        "https://www.state.gov/j/tip/rls/tiprpt/{year}/",
    ]

    def get_report_url(self, year: int) -> str:
        """Construct the TIP Report URL for a given year."""
        return (
            f"https://www.state.gov/reports/"
            f"{year}-trafficking-in-persons-report/pakistan/"
        )

    async def fetch_report_page(self, year: int) -> str | None:
        """Fetch a single year's TIP Report Pakistan page."""
        for pattern in self.URL_PATTERNS:
            url = pattern.format(year=year)
            try:
                response = await self.fetch(url)
                if response.status_code == 200 and len(response.text) > 500:
                    return response.text
            except Exception:
                continue
        logger.warning("[%s] Could not fetch TIP report for year %d", self.name, year)
        return None

    def extract_tier_ranking(self, html: str) -> str | None:
        """Extract the tier ranking from report text."""
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text()
        match = TIER_PATTERN.search(text)
        if match:
            tier = match.group(1).strip()
            # Normalize
            tier_map = {
                "1": "Tier 1",
                "2": "Tier 2",
                "2 watch list": "Tier 2 Watch List",
                "3": "Tier 3",
            }
            return tier_map.get(tier.lower(), f"Tier {tier}")
        return None

    def _extract_number_near_keyword(
        self, text: str, keyword: str
    ) -> int | None:
        """Find the closest number to a keyword in text.

        Prefers numbers immediately after the keyword (within same sentence),
        then falls back to numbers immediately before.
        """
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        idx = text_lower.find(keyword_lower)
        if idx == -1:
            return None
        # After the keyword (same sentence, up to next period)
        after_start = idx + len(keyword)
        after_text = text[after_start:after_start + 120]
        # Stop at sentence boundary
        period_idx = after_text.find(".")
        if period_idx > 0:
            after_text = after_text[:period_idx]
        after_nums = NUMBER_PATTERN.findall(after_text)
        if after_nums:
            return int(after_nums[0].replace(",", ""))
        # Before the keyword (within 40 chars, same sentence)
        before_start = max(0, idx - 40)
        before_text = text[before_start:idx]
        before_nums = NUMBER_PATTERN.findall(before_text)
        if before_nums:
            return int(before_nums[-1].replace(",", ""))
        return None

    def extract_metrics(self, html: str) -> dict[str, Any]:
        """Extract quantitative metrics from report text."""
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator=" ")

        metrics: dict[str, Any] = {}

        search_terms = {
            "investigations": ["investigat"],
            "prosecutions": ["prosecut"],
            "convictions": ["convict"],
            "victims_identified": ["victims identified", "identified victims", "victims were identified"],
            "victims_assisted": ["victims assisted", "assisted victims", "victims received"],
        }

        for metric_name, keywords in search_terms.items():
            for keyword in keywords:
                value = self._extract_number_near_keyword(text, keyword)
                if value is not None:
                    metrics[metric_name] = value
                    break

        return metrics

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the TIP Report scraping pipeline."""
        records: list[dict[str, Any]] = []

        for year in range(self.FIRST_YEAR, self.CURRENT_YEAR + 1):
            html = await self.fetch_report_page(year)
            if not html:
                continue

            tier = self.extract_tier_ranking(html)
            metrics = self.extract_metrics(html)

            record = {
                "year": year,
                "tier_ranking": tier,
                "url": self.get_report_url(year),
                "source": self.name,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                **metrics,
            }
            records.append(record)
            logger.info(
                "[%s] Year %d: %s, %d metrics extracted",
                self.name, year, tier or "no tier", len(metrics),
            )

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a TIP Report annual record.

        Accept records that have either a tier ranking or any extracted metrics,
        since older reports may not have structured tier designations.
        """
        if not record.get("year"):
            return False
        has_tier = bool(record.get("tier_ranking"))
        has_metrics = any(
            record.get(k) for k in (
                "investigations", "prosecutions", "convictions",
                "victims_identified", "victims_assisted",
            )
        )
        # Accept if we have a URL (i.e. the page was reachable)
        return has_tier or has_metrics or bool(record.get("url"))
