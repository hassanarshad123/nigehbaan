"""NCMEC (National Center for Missing & Exploited Children) report scraper.

Scrapes NCMEC annual data reports for CSAM/CyberTipline statistics,
particularly Pakistan-related data (5.4M reports 2020-2022).

URL: https://www.missingkids.org/content/ncmec/en/ourwork/ncmecdata.html
Schedule: Annually (0 3 15 3 *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

# Indicators of interest from NCMEC reports
_NCMEC_INDICATORS: list[str] = [
    "CyberTipline Reports",
    "CSAM Reports",
    "Reports from ESPs",
    "Reports by Country",
    "Pakistan",
    "Online Enticement",
    "Child Sex Trafficking",
    "Unsolicited Obscene Material",
]

_YEAR_PATTERN = re.compile(r"20[12]\d")
_NUMBER_PATTERN = re.compile(r"[\d,]+")


class NCMECScraper(BasePDFReportScraper):
    """Scraper for NCMEC annual data reports.

    Downloads PDF reports from the NCMEC data page, extracts tables
    containing CyberTipline statistics, and normalizes them into
    statistical_reports records with focus on Pakistan data.
    """

    name: str = "ncmec"
    source_url: str = (
        "https://www.missingkids.org/content/ncmec/en/ourwork/ncmecdata.html"
    )
    catalog_url: str = (
        "https://www.missingkids.org/content/ncmec/en/ourwork/ncmecdata.html"
    )
    schedule: str = "0 3 15 3 *"
    priority: str = "P1"
    rate_limit_delay: float = 3.0
    pdf_link_pattern: str = r"report.*\.pdf|data.*\.pdf"

    def _extract_year_from_url(self, pdf_url: str) -> int | None:
        """Extract report year from a PDF URL or filename."""
        match = _YEAR_PATTERN.search(pdf_url)
        return int(match.group()) if match else None

    def _parse_numeric(self, text: str) -> float | None:
        """Parse a numeric string, handling commas and whitespace."""
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None
        try:
            return float(cleaned) if "." in cleaned else float(int(cleaned))
        except ValueError:
            return None

    def _row_mentions_pakistan(self, row: list[str]) -> bool:
        """Check if a table row mentions Pakistan."""
        return any("pakistan" in cell.lower() for cell in row if cell)

    def _row_is_relevant(self, row: list[str]) -> bool:
        """Check if a table row contains CSAM/CyberTipline indicators."""
        row_text = " ".join(cell for cell in row if cell).lower()
        return any(ind.lower() in row_text for ind in _NCMEC_INDICATORS)

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Convert NCMEC PDF tables into statistical_reports records.

        Extracts both global CyberTipline stats and Pakistan-specific
        country breakdowns.

        Args:
            tables: Raw tables from PDF extraction.
            pdf_url: Source URL for provenance.

        Returns:
            List of normalized statistical_reports records.
        """
        report_year = self._extract_year_from_url(pdf_url)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        for table in tables:
            if len(table) < 2:
                continue

            headers = table[0]
            for row in table[1:]:
                if not self._row_is_relevant(row) and not self._row_mentions_pakistan(row):
                    continue

                # Determine indicator from first non-empty cell
                indicator = ""
                value = None
                for i, cell in enumerate(row):
                    cell_text = cell.strip() if cell else ""
                    if not cell_text:
                        continue
                    parsed = self._parse_numeric(cell_text)
                    if parsed is not None and not indicator:
                        # First numeric cell without an indicator is just a number
                        continue
                    if parsed is not None:
                        value = parsed
                        break
                    if not indicator:
                        indicator = cell_text

                if not indicator:
                    continue

                geographic_scope = (
                    "Pakistan" if self._row_mentions_pakistan(row)
                    else "Global"
                )

                records.append({
                    "source_name": "NCMEC",
                    "report_year": report_year,
                    "report_title": "NCMEC Annual Data Report",
                    "indicator": indicator,
                    "value": value,
                    "unit": "reports",
                    "geographic_scope": geographic_scope,
                    "pdf_url": pdf_url,
                    "extraction_method": "pdfplumber_table",
                    "scraped_at": now,
                })

        # If no table-based records found, try text extraction
        if not records:
            records = self._extract_from_text(pdf_url, report_year)

        return records

    def _extract_from_text(
        self, pdf_url: str, report_year: int | None
    ) -> list[dict[str, Any]]:
        """Fallback: extract key statistics from PDF text using regex."""
        raw_dir = self.get_raw_dir()
        filename = pdf_url.split("/")[-1].split("?")[0]
        pdf_path = raw_dir / filename

        if not pdf_path.exists():
            return []

        text = self.extract_text(pdf_path)
        if not text:
            return []

        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        # Search for Pakistan-specific data
        pakistan_patterns = [
            (r"Pakistan.*?(\d[\d,]+)\s*reports?", "CyberTipline Reports - Pakistan"),
            (r"(\d[\d,]+)\s*reports?.*?Pakistan", "CyberTipline Reports - Pakistan"),
        ]

        for pattern, indicator in pakistan_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = self._parse_numeric(match.group(1))
                if value:
                    records.append({
                        "source_name": "NCMEC",
                        "report_year": report_year,
                        "report_title": "NCMEC Annual Data Report",
                        "indicator": indicator,
                        "value": value,
                        "unit": "reports",
                        "geographic_scope": "Pakistan",
                        "pdf_url": pdf_url,
                        "extraction_method": "text_regex",
                        "scraped_at": now,
                    })
                    break

        # Global totals
        global_patterns = [
            (r"(\d[\d,]+)\s*(?:total\s+)?CyberTipline\s+reports", "Total CyberTipline Reports"),
            (r"CyberTipline.*?received\s+(\d[\d,]+)", "Total CyberTipline Reports"),
            (r"(\d[\d,]+)\s*(?:total\s+)?CSAM", "CSAM Reports"),
        ]

        for pattern, indicator in global_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = self._parse_numeric(match.group(1))
                if value:
                    records.append({
                        "source_name": "NCMEC",
                        "report_year": report_year,
                        "report_title": "NCMEC Annual Data Report",
                        "indicator": indicator,
                        "value": value,
                        "unit": "reports",
                        "geographic_scope": "Global",
                        "pdf_url": pdf_url,
                        "extraction_method": "text_regex",
                        "scraped_at": now,
                    })

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a statistical_reports record from NCMEC.

        Requires source_name and indicator at minimum. Value can
        be None if the report mentions a qualitative finding.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
            and record.get("pdf_url")
        )
