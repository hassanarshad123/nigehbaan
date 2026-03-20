"""Google Transparency Report scraper.

Scrapes Google's transparency report for government content removal
requests, focusing on Pakistan-specific data related to child safety
and online exploitation.

URL: https://transparencyreport.google.com/government-removals/overview
Schedule: Semi-annually (0 3 1 2,8 *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from data.scrapers.base_html_scraper import BaseHTMLTableScraper

logger = logging.getLogger(__name__)

_PERIOD_PATTERN = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"(?:uary|ruary|ch|il|e|ust|tember|ober|ember)?\s*"
    r"(\d{4})\s*[-–]\s*"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"(?:uary|ruary|ch|il|e|ust|tember|ober|ember)?\s*"
    r"(\d{4})",
    re.IGNORECASE,
)

_HALF_PATTERN = re.compile(r"H([12])\s*(\d{4})")

# Google products relevant to child safety
_RELEVANT_PRODUCTS: list[str] = [
    "youtube",
    "google search",
    "google+",
    "blogger",
    "google play",
    "google photos",
    "google drive",
    "gmail",
]


class GoogleTransparencyScraper(BaseHTMLTableScraper):
    """Scraper for Google Transparency Reports.

    Extracts government content removal request data from Google's
    transparency portal, filtering for Pakistan and child-safety
    related categories.
    """

    name: str = "google_transparency"
    source_url: str = (
        "https://transparencyreport.google.com/government-removals/overview"
    )
    schedule: str = "0 3 1 2,8 *"
    priority: str = "P1"
    rate_limit_delay: float = 3.0

    # Pakistan-specific URL path
    _pakistan_url: str = (
        "https://transparencyreport.google.com/"
        "government-removals/by-country/PK"
    )

    # CSAM/child safety specific URL
    _csam_url: str = (
        "https://transparencyreport.google.com/"
        "child-sexual-abuse-material"
    )

    def _extract_period(self, text: str) -> str | None:
        """Extract the reporting period from page text."""
        match = _HALF_PATTERN.search(text)
        if match:
            return f"H{match.group(1)} {match.group(2)}"
        match = _PERIOD_PATTERN.search(text)
        if match:
            return f"{match.group(1)} {match.group(2)} - {match.group(3)} {match.group(4)}"
        return None

    def _parse_numeric(self, text: str) -> float | None:
        """Parse a numeric value from a string, handling M/K suffixes."""
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None
        if cleaned.endswith("%"):
            try:
                return float(cleaned[:-1])
            except ValueError:
                return None
        multipliers = {"M": 1_000_000, "K": 1_000, "B": 1_000_000_000}
        for suffix, multiplier in multipliers.items():
            if cleaned.upper().endswith(suffix):
                try:
                    return float(cleaned[:-1]) * multiplier
                except ValueError:
                    return None
        try:
            return float(cleaned) if "." in cleaned else float(int(cleaned))
        except ValueError:
            return None

    def _is_child_safety_related(self, text: str) -> bool:
        """Check if text is related to child safety or CSAM."""
        keywords = [
            "child", "csam", "sexual exploitation", "minor",
            "child sexual abuse", "child safety", "child endangerment",
            "pornograph",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)

    def _infer_unit(self, metric: str, raw_value: str) -> str:
        """Infer measurement unit from metric name and raw value."""
        metric_lower = metric.lower()
        if "%" in raw_value or "rate" in metric_lower or "percent" in metric_lower:
            return "percent"
        if "request" in metric_lower:
            return "requests"
        if "item" in metric_lower or "content" in metric_lower:
            return "items"
        if "url" in metric_lower:
            return "URLs"
        return "count"

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the Google transparency report scraping pipeline.

        Fetches the overview, Pakistan-specific page, and CSAM
        reporting page, then extracts metrics from HTML tables.
        """
        all_records: list[dict[str, Any]] = []

        # 1. Fetch Pakistan-specific government removal data
        try:
            pk_response = await self.fetch(self._pakistan_url)
            pk_records = self._extract_country_data(
                pk_response.text, self._pakistan_url
            )
            all_records.extend(pk_records)
        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch Pakistan page: %s", self.name, exc
            )

        # 2. Fetch CSAM-specific reporting page
        try:
            csam_response = await self.fetch(self._csam_url)
            csam_records = self._extract_csam_data(
                csam_response.text, self._csam_url
            )
            all_records.extend(csam_records)
        except Exception as exc:
            logger.warning(
                "[%s] Failed to fetch CSAM page: %s", self.name, exc
            )

        # 3. Fetch main overview for global child safety data
        try:
            overview_response = await self.fetch(self.source_url)
            overview_records = self._extract_overview_data(
                overview_response.text
            )
            all_records.extend(overview_records)
        except Exception as exc:
            logger.warning(
                "[%s] Failed to fetch overview: %s", self.name, exc
            )

        return all_records

    def _extract_country_data(
        self, html: str, url: str
    ) -> list[dict[str, Any]]:
        """Extract Pakistan-specific government removal request data."""
        tables = self.extract_tables(html)
        now = datetime.now(timezone.utc).isoformat()
        period = self._extract_period(html)
        records: list[dict[str, Any]] = []

        for table in tables:
            for row in table:
                for key, value_str in row.items():
                    if not value_str:
                        continue
                    value = self._parse_numeric(value_str)
                    if value is not None:
                        records.append({
                            "platform": "Google",
                            "report_period": period,
                            "country": "Pakistan",
                            "metric": key,
                            "value": value,
                            "unit": self._infer_unit(key, value_str),
                            "source_url": url,
                            "scraped_at": now,
                        })

        # Also extract from text if tables are sparse
        if not records:
            text_records = self._extract_from_text(
                html, url, country="Pakistan"
            )
            records.extend(text_records)

        return records

    def _extract_csam_data(
        self, html: str, url: str
    ) -> list[dict[str, Any]]:
        """Extract CSAM-specific data from Google's child safety page."""
        tables = self.extract_tables(html)
        now = datetime.now(timezone.utc).isoformat()
        period = self._extract_period(html)
        records: list[dict[str, Any]] = []

        for table in tables:
            for row in table:
                country = "Global"
                for key, val in row.items():
                    if isinstance(val, str) and "pakistan" in val.lower():
                        country = "Pakistan"
                        break

                for key, value_str in row.items():
                    if not value_str:
                        continue
                    value = self._parse_numeric(value_str)
                    if value is not None:
                        records.append({
                            "platform": "Google",
                            "report_period": period,
                            "country": country,
                            "metric": f"CSAM - {key}",
                            "value": value,
                            "unit": self._infer_unit(key, value_str),
                            "source_url": url,
                            "scraped_at": now,
                        })

        return records

    def _extract_overview_data(self, html: str) -> list[dict[str, Any]]:
        """Extract child-safety-related rows from the overview page."""
        tables = self.extract_tables(html)
        now = datetime.now(timezone.utc).isoformat()
        period = self._extract_period(html)
        records: list[dict[str, Any]] = []

        for table in tables:
            for row in table:
                row_text = " ".join(str(v) for v in row.values())
                if not self._is_child_safety_related(row_text):
                    continue

                country = "Global"
                for key, val in row.items():
                    if isinstance(val, str) and "pakistan" in val.lower():
                        country = "Pakistan"
                        break

                for key, value_str in row.items():
                    if not value_str:
                        continue
                    value = self._parse_numeric(value_str)
                    if value is not None:
                        records.append({
                            "platform": "Google",
                            "report_period": period,
                            "country": country,
                            "metric": key,
                            "value": value,
                            "unit": self._infer_unit(key, value_str),
                            "source_url": self.source_url,
                            "scraped_at": now,
                        })

        return records

    def _extract_from_text(
        self, html: str, url: str, country: str = "Global"
    ) -> list[dict[str, Any]]:
        """Fallback: extract key metrics from page text via regex."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ")
        now = datetime.now(timezone.utc).isoformat()
        period = self._extract_period(text)
        records: list[dict[str, Any]] = []

        patterns = {
            "Removal Requests": r"(\d[\d,]*)\s*(?:removal\s+)?requests?",
            "Items Requested for Removal": r"(\d[\d,]*)\s*items?\s*(?:requested|flagged)",
            "Items Removed": r"(\d[\d,]*)\s*items?\s*removed",
            "Compliance Rate": r"(\d+(?:\.\d+)?)\s*%\s*(?:compliance|removal\s*rate)",
        }

        for metric, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = self._parse_numeric(match.group(1))
                if value is not None:
                    records.append({
                        "platform": "Google",
                        "report_period": period,
                        "country": country,
                        "metric": metric,
                        "value": value,
                        "unit": self._infer_unit(metric, match.group(0)),
                        "source_url": url,
                        "scraped_at": now,
                    })

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a transparency_reports record from Google.

        Requires platform, metric, and a non-None value.
        """
        return bool(
            record.get("platform")
            and record.get("metric")
            and record.get("value") is not None
        )
