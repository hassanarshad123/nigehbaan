"""Meta Transparency Report scraper.

Scrapes Meta's Community Standards Enforcement Reports for CSAM
content moderation statistics, with focus on Pakistan data and
global child safety metrics.

URL: https://transparency.meta.com/reports/community-standards-enforcement
Schedule: Semi-annually (0 3 1 1,7 *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin
import re

import logging

from data.scrapers.base_html_scraper import BaseHTMLTableScraper

logger = logging.getLogger(__name__)

_QUARTER_PATTERN = re.compile(r"Q([1-4])\s*(\d{4})")
_PERIOD_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+(\d{4})\s*[-–]\s*"
    r"(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+(\d{4})",
    re.IGNORECASE,
)

# Metrics of interest from Meta's CSAM enforcement reports
_META_CSAM_METRICS: list[str] = [
    "child nudity and sexual exploitation",
    "child sexual exploitation",
    "child endangerment",
    "child exploitative",
    "CSAM",
    "content actioned",
    "content removed",
    "appeals",
    "restored",
    "proactive rate",
]


class MetaTransparencyScraper(BaseHTMLTableScraper):
    """Scraper for Meta Transparency Reports on child safety.

    Extracts CSAM enforcement metrics from Meta's transparency
    portal, including content actioned, proactive detection rate,
    and appeals data, filtered for Pakistan where available.
    """

    name: str = "meta_transparency"
    source_url: str = (
        "https://transparency.meta.com/reports/community-standards-enforcement"
    )
    schedule: str = "0 3 1 1,7 *"
    priority: str = "P1"
    rate_limit_delay: float = 3.0

    # Child safety report sections to target
    _report_sections: list[str] = [
        "/child-nudity-and-sexual-exploitation/",
        "/child-sexual-exploitation/",
        "/child-endangerment-nudity-and-physical-abuse/",
    ]

    def _build_section_urls(self) -> list[str]:
        """Build URLs for child-safety-related report sections."""
        base = self.source_url.rstrip("/")
        return [f"{base}{section}" for section in self._report_sections]

    def _extract_period(self, text: str) -> str | None:
        """Extract the reporting period from page text."""
        match = _QUARTER_PATTERN.search(text)
        if match:
            return f"Q{match.group(1)} {match.group(2)}"
        match = _PERIOD_PATTERN.search(text)
        if match:
            return f"{match.group(1)} {match.group(2)} - {match.group(3)} {match.group(4)}"
        return None

    def _parse_numeric(self, text: str) -> float | None:
        """Parse a numeric value from a string, handling M/K suffixes."""
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None
        # Handle percentage
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]
            try:
                return float(cleaned)
            except ValueError:
                return None
        # Handle M/K suffixes (e.g., "2.3M", "450K")
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

    def _is_csam_related(self, text: str) -> bool:
        """Check whether text relates to CSAM / child safety metrics."""
        text_lower = text.lower()
        return any(metric.lower() in text_lower for metric in _META_CSAM_METRICS)

    def _infer_unit(self, metric_text: str, value_text: str) -> str:
        """Infer the measurement unit from metric name and value text."""
        if "%" in value_text or "rate" in metric_text.lower():
            return "percent"
        if "appeal" in metric_text.lower():
            return "appeals"
        if "piece" in metric_text.lower() or "content" in metric_text.lower():
            return "content_pieces"
        return "count"

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the Meta transparency report scraping pipeline.

        Fetches the main report page and child-safety subsections,
        extracts tables and CSV download links, and normalizes records.
        """
        all_records: list[dict[str, Any]] = []

        # Fetch main page for overview data and CSV links
        try:
            main_response = await self.fetch(self.source_url)
            main_html = main_response.text
            overview_records = self._extract_overview(main_html)
            all_records.extend(overview_records)

            # Look for CSV download links
            csv_links = self.extract_links(main_html, r"\.csv")
            for link in csv_links:
                csv_records = await self._process_csv_link(link)
                all_records.extend(csv_records)
        except Exception as exc:
            logger.error("[%s] Failed to fetch main page: %s", self.name, exc)

        # Fetch child-safety-specific sections
        section_urls = self._build_section_urls()
        for section_url in section_urls:
            try:
                response = await self.fetch(section_url)
                section_records = self._extract_section_data(
                    response.text, section_url
                )
                all_records.extend(section_records)
            except Exception as exc:
                logger.warning(
                    "[%s] Failed to fetch section %s: %s",
                    self.name, section_url, exc,
                )

        return all_records

    def _extract_overview(self, html: str) -> list[dict[str, Any]]:
        """Extract child-safety metrics from the main overview page."""
        tables = self.extract_tables(html)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []
        period = self._extract_period(html)

        for table in tables:
            for row in table:
                row_text = " ".join(str(v) for v in row.values())
                if not self._is_csam_related(row_text):
                    continue

                for key, value_str in row.items():
                    value = self._parse_numeric(value_str)
                    if value is not None:
                        records.append({
                            "platform": "Meta",
                            "report_period": period,
                            "country": "Global",
                            "metric": key,
                            "value": value,
                            "unit": self._infer_unit(key, value_str),
                            "source_url": self.source_url,
                            "scraped_at": now,
                        })

        return records

    def _extract_section_data(
        self, html: str, section_url: str
    ) -> list[dict[str, Any]]:
        """Extract metrics from a child-safety section page."""
        tables = self.extract_tables(html)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []
        period = self._extract_period(html)

        # Determine section name from URL
        section_name = section_url.rstrip("/").split("/")[-1].replace("-", " ").title()

        for table in tables:
            for row in table:
                # Check for Pakistan-specific rows
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
                        metric = f"{section_name} - {key}"
                        records.append({
                            "platform": "Meta",
                            "report_period": period,
                            "country": country,
                            "metric": metric,
                            "value": value,
                            "unit": self._infer_unit(key, value_str),
                            "source_url": section_url,
                            "scraped_at": now,
                        })

        return records

    async def _process_csv_link(
        self, link: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Download and parse a CSV file linked from the report page."""
        import csv
        import io

        url = link.get("url", "")
        if not url.startswith("http"):
            url = urljoin(self.source_url, url)

        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        try:
            response = await self.fetch(url)
            reader = csv.DictReader(io.StringIO(response.text))

            for row in reader:
                row_text = " ".join(str(v) for v in row.values())
                if not self._is_csam_related(row_text):
                    continue

                country = row.get("country", row.get("Country", "Global"))
                # Filter for Pakistan or keep all for global metrics
                period = (
                    row.get("period", "")
                    or row.get("Period", "")
                    or row.get("date_range", "")
                )

                for key, value_str in row.items():
                    if key.lower() in ("country", "period", "date_range"):
                        continue
                    if not value_str:
                        continue
                    value = self._parse_numeric(value_str)
                    if value is not None:
                        records.append({
                            "platform": "Meta",
                            "report_period": period or None,
                            "country": country,
                            "metric": key,
                            "value": value,
                            "unit": self._infer_unit(key, value_str),
                            "source_url": url,
                            "scraped_at": now,
                        })
        except Exception as exc:
            logger.warning("[%s] Failed to process CSV %s: %s", self.name, url, exc)

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a transparency_reports record from Meta.

        Requires platform, metric, and a non-None value.
        """
        return bool(
            record.get("platform")
            and record.get("metric")
            and record.get("value") is not None
        )
