"""CPWB Punjab (Child Protection & Welfare Bureau) scraper.

Scrapes cpwb.punjab.gov.pk for Helpline 1121 statistics, child rescue
data, and rehabilitation center information from the Punjab Child
Protection & Welfare Bureau.

URL: https://cpwb.punjab.gov.pk
Schedule: Quarterly (0 3 1 */3 *)
Priority: P2
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
import re

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_html_scraper import BaseHTMLTableScraper

logger = logging.getLogger(__name__)

# Expected CPWB indicators
CPWB_INDICATORS: list[str] = [
    "helpline_1121_calls",
    "children_rescued",
    "children_reunited",
    "children_in_shelters",
    "fir_registered",
    "child_labor_rescued",
    "begging_children_rescued",
    "sexual_abuse_cases",
    "physical_abuse_cases",
    "kidnapping_cases",
    "missing_children_recovered",
    "rehabilitation_cases",
    "counseling_sessions",
    "legal_aid_cases",
]


class CPWBPunjabScraper(BaseHTMLTableScraper):
    """Scraper for Punjab Child Protection & Welfare Bureau data.

    Extracts Helpline 1121 call statistics, child rescue operations
    data, shelter/rehabilitation center statistics, and case resolution
    metrics from the CPWB Punjab website.
    """

    name: str = "cpwb_punjab"
    source_url: str = "https://cpwb.punjab.gov.pk"
    schedule: str = "0 3 1 */3 *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0

    # Known CPWB pages with statistical data
    DATA_PAGES: list[str] = [
        "https://cpwb.punjab.gov.pk",
        "https://cpwb.punjab.gov.pk/statistics",
        "https://cpwb.punjab.gov.pk/achievements",
        "https://cpwb.punjab.gov.pk/helpline-1121",
        "https://cpwb.punjab.gov.pk/child-protection-units",
        "https://cpwb.punjab.gov.pk/report",
    ]

    def _classify_indicator(self, text: str) -> str:
        """Map raw text to a standardized CPWB indicator.

        Args:
            text: Raw text from table cell or heading.

        Returns:
            Standardized indicator name.
        """
        text_lower = text.lower()

        mapping: dict[str, list[str]] = {
            "helpline_1121_calls": ["helpline", "1121", "call received", "phone call"],
            "children_rescued": ["child rescued", "rescue", "children rescued"],
            "children_reunited": ["reunited", "reunif", "handed over", "returned to family"],
            "children_in_shelters": ["shelter", "center", "centre", "housed"],
            "fir_registered": ["fir", "first information report", "case registered", "police report"],
            "child_labor_rescued": ["child lab", "labor rescue", "labour rescue", "bonded"],
            "begging_children_rescued": ["begging", "begg", "street"],
            "sexual_abuse_cases": ["sexual abuse", "rape", "sodomy", "molestation"],
            "physical_abuse_cases": ["physical abuse", "torture", "beating", "violence"],
            "kidnapping_cases": ["kidnap", "abduct", "missing"],
            "missing_children_recovered": ["missing", "recovered", "found"],
            "rehabilitation_cases": ["rehabilitat", "recovery program"],
            "counseling_sessions": ["counsel", "therapy", "psycho"],
            "legal_aid_cases": ["legal", "lawyer", "court", "prosecution"],
        }

        for indicator, keywords in mapping.items():
            if any(kw in text_lower for kw in keywords):
                return indicator

        return text.strip()[:100]

    def _parse_numeric(self, text: str) -> int | float | None:
        """Parse a numeric value from a string.

        Args:
            text: Raw cell text.

        Returns:
            Numeric value or None.
        """
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None

        # Handle "1,234+" or "5000+" patterns
        cleaned = cleaned.rstrip("+")

        try:
            if "." in cleaned:
                return float(cleaned)
            return int(cleaned)
        except ValueError:
            return None

    def _extract_year(self, text: str) -> int | None:
        """Extract year from text.

        Args:
            text: Text to search.

        Returns:
            Year or None.
        """
        year_match = re.search(r"20[0-2]\d", text)
        if year_match:
            return int(year_match.group())
        return None

    def _parse_table_records(
        self, table_data: list[dict[str, str]], page_url: str
    ) -> list[dict[str, Any]]:
        """Convert HTML table rows into statistical_reports records.

        Args:
            table_data: List of row-dicts from BaseHTMLTableScraper.extract_tables().
            page_url: Source page URL for provenance.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for row in table_data:
            # Find the indicator column (first text column)
            indicator_text = ""
            value = None
            province = None
            gender = None
            year = None

            for header, cell in row.items():
                header_lower = header.lower()

                if any(kw in header_lower for kw in [
                    "category", "type", "indicator", "description",
                    "offence", "crime", "activity",
                ]):
                    indicator_text = cell
                elif any(kw in header_lower for kw in ["total", "count", "number", "cases"]):
                    value = self._parse_numeric(cell)
                elif any(kw in header_lower for kw in ["province", "district", "region"]):
                    province = self.normalize_province(cell)
                elif any(kw in header_lower for kw in ["male", "boy"]):
                    if self._parse_numeric(cell) is not None:
                        gender = "male"
                        value = self._parse_numeric(cell)
                elif any(kw in header_lower for kw in ["female", "girl"]):
                    if self._parse_numeric(cell) is not None:
                        gender = "female"
                        value = self._parse_numeric(cell)
                elif "year" in header_lower:
                    year = self._extract_year(cell)

            # If no indicator column was found, use first column
            if not indicator_text and row:
                first_key = next(iter(row))
                indicator_text = row[first_key]

            if not indicator_text:
                continue

            # If no value found yet, try to find any numeric cell
            if value is None:
                for cell in row.values():
                    value = self._parse_numeric(cell)
                    if value is not None:
                        break

            if value is None:
                continue

            indicator = self._classify_indicator(indicator_text)

            records.append({
                "source_name": self.name,
                "report_year": year or now.year,
                "report_title": f"CPWB Punjab Statistics {year or now.year}",
                "indicator": indicator,
                "value": value,
                "unit": "cases",
                "geographic_scope": province or "Punjab",
                "victim_gender": gender,
                "victim_age_bracket": "0-18",
                "pdf_url": page_url,
                "extraction_method": "html_table",
                "extraction_confidence": 0.8,
                "scraped_at": now.isoformat(),
            })

        return records

    def _extract_stat_blocks(self, html: str, page_url: str) -> list[dict[str, Any]]:
        """Extract statistics from infographic/stat blocks on the page.

        Many government sites display key metrics in styled div blocks
        rather than tables.

        Args:
            html: Raw HTML content.
            page_url: Source page URL.

        Returns:
            List of statistical_reports records.
        """
        soup = BeautifulSoup(html, "html.parser")
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Look for counter/stat blocks
        stat_selectors = [
            {"class_": re.compile(r"stat|counter|fact|figure|number|achievement", re.IGNORECASE)},
            {"class_": re.compile(r"count|metric|kpi", re.IGNORECASE)},
        ]

        for selector in stat_selectors:
            for block in soup.find_all(["div", "section", "li"], **selector):
                text = block.get_text(strip=True)
                if not text or len(text) > 500:
                    continue

                # Look for number + label pattern
                number_match = re.search(r"([\d,]+)\s*\+?\s*(.+)", text)
                if not number_match:
                    number_match = re.search(r"(.+?)\s*([\d,]+)", text)
                    if number_match:
                        label = number_match.group(1).strip()
                        raw_value = number_match.group(2)
                    else:
                        continue
                else:
                    raw_value = number_match.group(1)
                    label = number_match.group(2).strip()

                value = self._parse_numeric(raw_value)
                if value is None or value == 0:
                    continue

                indicator = self._classify_indicator(label)

                records.append({
                    "source_name": self.name,
                    "report_year": now.year,
                    "report_title": f"CPWB Punjab Website Statistics {now.year}",
                    "indicator": indicator,
                    "value": value,
                    "unit": "cases",
                    "geographic_scope": "Punjab",
                    "victim_gender": None,
                    "victim_age_bracket": "0-18",
                    "pdf_url": page_url,
                    "extraction_method": "html_stat_block",
                    "extraction_confidence": 0.65,
                    "scraped_at": now.isoformat(),
                })

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch CPWB Punjab pages, extract tables and stat blocks.

        Iterates through known data pages, extracting HTML tables
        and infographic stat blocks. Normalizes province names
        throughout.

        Returns:
            List of statistical_reports records.
        """
        all_records: list[dict[str, Any]] = []

        for page_url in self.DATA_PAGES:
            try:
                response = await self.fetch(page_url)
                html = response.text

                # Extract tables using base class method
                tables = self.extract_tables(html)
                for table_data in tables:
                    records = self._parse_table_records(table_data, page_url)
                    all_records.extend(records)

                # Extract stat blocks
                stat_records = self._extract_stat_blocks(html, page_url)
                all_records.extend(stat_records)

                logger.info(
                    "[%s] Page %s: %d table records, %d stat block records",
                    self.name, page_url,
                    len(all_records) - len(stat_records), len(stat_records),
                )
            except Exception as exc:
                logger.warning("[%s] Failed to fetch %s: %s", self.name, page_url, exc)

        # Deduplicate by (indicator, value, year) tuple
        seen: set[tuple[str, Any, Any]] = set()
        unique_records: list[dict[str, Any]] = []
        for record in all_records:
            key = (
                record.get("indicator", ""),
                record.get("value"),
                record.get("report_year"),
            )
            if key not in seen:
                seen.add(key)
                unique_records.append(record)

        logger.info("[%s] Total unique records: %d", self.name, len(unique_records))
        return unique_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a CPWB Punjab statistical report record.

        Requires source_name and a non-empty indicator.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
        )
