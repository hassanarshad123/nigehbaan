"""Bonded Labour Liberation Front (BLLF) Pakistan website scraper.

Extracts data from BLLF's website about bonded labourers freed across
Pakistan. BLLF has facilitated the release of 85,000+ bonded labourers,
approximately 45% of whom are children. Data includes rescue operations,
brick kiln raids, and rehabilitation statistics.

Source: https://bllfpk.com
Schedule: Annually (0 8 1 4 *)
Priority: P2 — Key civil society data on bonded child labor
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import logging
import re

from data.scrapers.base_html_scraper import BaseHTMLTableScraper

logger = logging.getLogger(__name__)

# Keywords for identifying relevant tables/content
_BLLF_KEYWORDS: list[str] = [
    "bonded",
    "freed",
    "released",
    "rescued",
    "labourers",
    "laborers",
    "children",
    "brick kiln",
    "bhatta",
    "rehabilitation",
    "raid",
    "recovery",
]


class BLLFScraper(BaseHTMLTableScraper):
    """Scraper for Bonded Labour Liberation Front Pakistan website.

    Fetches the BLLF homepage and key sub-pages, extracts HTML tables
    containing statistics about bonded labourers freed (including
    children), and maps rows to statistical_reports records.
    """

    name: str = "bllf"
    source_url: str = "https://bllfpk.com"
    schedule: str = "0 8 1 4 *"
    priority: str = "P2"
    rate_limit_delay: float = 3.0
    request_timeout: float = 45.0

    # Sub-pages likely to contain statistical tables
    _sub_paths: list[str] = [
        "/",
        "/about",
        "/about-us",
        "/achievements",
        "/statistics",
        "/reports",
        "/our-work",
        "/programs",
    ]

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch BLLF pages, extract tables, and produce records."""
        base_url = self.source_url.rstrip("/")
        all_records: list[dict[str, Any]] = []

        for path in self._sub_paths:
            url = f"{base_url}{path}"
            try:
                response = await self.fetch(url)
                tables = self.extract_tables(response.text)
                records = self._process_tables(tables, url)
                all_records.extend(records)

                # Also extract inline statistics from page text
                text_records = self._extract_inline_stats(response.text, url)
                all_records.extend(text_records)

            except Exception as exc:
                logger.debug(
                    "[%s] Could not fetch %s: %s", self.name, url, exc
                )
                continue

        # Deduplicate by indicator + geographic_scope
        all_records = self._deduplicate(all_records)
        return all_records

    def _process_tables(
        self, tables: list[list[dict[str, str]]], page_url: str
    ) -> list[dict[str, Any]]:
        """Process extracted HTML tables into statistical_reports records."""
        records: list[dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for table in tables:
            if not table:
                continue

            # Check if table is relevant
            sample_text = " ".join(
                str(v).lower()
                for row in table[:5]
                for v in row.values()
            )
            if not any(kw in sample_text for kw in _BLLF_KEYWORDS):
                continue

            for row in table:
                indicator = self._build_indicator(row)
                value = self._extract_value(row)

                if not indicator:
                    continue

                province = self._detect_province(row)

                records.append({
                    "source_name": self.name,
                    "report_year": self._extract_year(row),
                    "report_title": "BLLF Bonded Labour Statistics",
                    "indicator": indicator,
                    "value": value,
                    "unit": "count",
                    "geographic_scope": province or "Pakistan",
                    "pdf_url": None,
                    "extraction_method": "html_table",
                    "extraction_confidence": 0.70,
                    "victim_gender": self._detect_gender(row),
                    "victim_age_bracket": None,
                    "page_url": page_url,
                    "scraped_at": now_iso,
                })

        return records

    def _extract_inline_stats(
        self, html: str, page_url: str
    ) -> list[dict[str, Any]]:
        """Extract statistics embedded in page text (not in tables)."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        records: list[dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # Pattern: "85,000+ bonded labourers freed"
        patterns = [
            (
                re.compile(
                    r"([\d,]+)\s*\+?\s*(?:bonded\s+)?(?:labourers?|laborers?|workers?)\s+(?:freed|released|rescued)",
                    re.IGNORECASE,
                ),
                "bonded_labourers_freed",
            ),
            (
                re.compile(
                    r"([\d,]+)\s*\+?\s*children\s+(?:freed|released|rescued|rehabilitated)",
                    re.IGNORECASE,
                ),
                "children_freed",
            ),
            (
                re.compile(
                    r"(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:them\s+)?(?:are\s+)?children",
                    re.IGNORECASE,
                ),
                "children_percentage",
            ),
            (
                re.compile(
                    r"([\d,]+)\s*\+?\s*(?:brick\s+)?kilns?\s+(?:raided|inspected|surveyed)",
                    re.IGNORECASE,
                ),
                "kilns_raided",
            ),
        ]

        for pattern, indicator in patterns:
            for match in pattern.finditer(text):
                value_str = match.group(1).replace(",", "")
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                unit = "percent" if "percentage" in indicator else "count"

                records.append({
                    "source_name": self.name,
                    "report_year": str(datetime.now(timezone.utc).year),
                    "report_title": "BLLF Bonded Labour Statistics",
                    "indicator": indicator,
                    "value": value,
                    "unit": unit,
                    "geographic_scope": "Pakistan",
                    "pdf_url": None,
                    "extraction_method": "html_text_regex",
                    "extraction_confidence": 0.60,
                    "victim_gender": None,
                    "victim_age_bracket": None,
                    "page_url": page_url,
                    "scraped_at": now_iso,
                })

        return records

    @staticmethod
    def _build_indicator(row: dict[str, str]) -> str:
        """Build an indicator name from the first non-numeric cell."""
        for key, value in row.items():
            cleaned = str(value).strip()
            if cleaned and not cleaned.replace(",", "").replace(".", "").isdigit():
                return f"bllf_{cleaned[:80]}".replace(" ", "_").lower()
        return ""

    @staticmethod
    def _extract_value(row: dict[str, str]) -> float | None:
        """Extract the first numeric value from a row."""
        for value in row.values():
            cleaned = str(value).replace(",", "").strip()
            if not cleaned:
                continue
            try:
                return float(cleaned)
            except ValueError:
                continue
        return None

    def _detect_province(self, row: dict[str, str]) -> str | None:
        """Detect province from row values using normalize_province."""
        for value in row.values():
            normalized = self.normalize_province(str(value).strip())
            if normalized != str(value).strip():
                return normalized
            # Direct match check
            val_lower = str(value).strip().lower()
            if val_lower in (
                "punjab", "sindh", "balochistan", "kp", "kpk",
                "khyber pakhtunkhwa", "islamabad",
            ):
                return self.normalize_province(val_lower)
        return None

    @staticmethod
    def _detect_gender(row: dict[str, str]) -> str | None:
        """Detect gender from row values."""
        combined = " ".join(str(v).lower() for v in row.values())
        if "female" in combined or "girl" in combined or "women" in combined:
            return "female"
        if "male" in combined or "boy" in combined:
            if "female" not in combined:
                return "male"
        return None

    @staticmethod
    def _extract_year(row: dict[str, str]) -> str:
        """Extract a year from any cell in the row."""
        for value in row.values():
            match = re.search(r"20[0-2]\d", str(value))
            if match:
                return match.group()
        return str(datetime.now(timezone.utc).year)

    @staticmethod
    def _deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate records by indicator + geographic_scope."""
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for record in records:
            key = f"{record.get('indicator', '')}|{record.get('geographic_scope', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(record)
        return unique

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a BLLF record."""
        if not record.get("source_name"):
            return False
        if not record.get("indicator"):
            return False
        # Value can be None for text-based entries
        return True
