"""IWF (Internet Watch Foundation) annual report scraper.

Scrapes IWF annual reports for CSAM statistics — 275K+ confirmed
CSAM URLs tracked globally.

URL: https://www.iwf.org.uk/about-us/who-we-are/annual-reports/
Schedule: Annually (0 3 1 5 *)
Priority: P1
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import re

import logging

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

_YEAR_PATTERN = re.compile(r"20[12]\d")
_NUMBER_PATTERN = re.compile(r"([\d,]+(?:\.\d+)?)")

# Key IWF metrics to extract
_IWF_METRICS: dict[str, list[str]] = {
    "Confirmed CSAM URLs": [
        r"(\d[\d,]+)\s*(?:confirmed\s+)?(?:URLs?|webpages?)",
        r"confirmed.*?(\d[\d,]+)\s*(?:URLs?|webpages?)",
    ],
    "Actioned Reports": [
        r"(\d[\d,]+)\s*(?:actioned\s+)?reports?\s*(?:were\s+)?actioned",
        r"actioned\s+(\d[\d,]+)\s*reports?",
    ],
    "Self-Generated CSAM": [
        r"self[- ]generated.*?(\d[\d,]+)",
        r"(\d[\d,]+).*?self[- ]generated",
    ],
    "Category A Images": [
        r"category\s*A.*?(\d[\d,]+)",
        r"(\d[\d,]+).*?category\s*A",
    ],
    "Reports Assessed": [
        r"(\d[\d,]+)\s*reports?\s*(?:were\s+)?assessed",
        r"assessed\s+(\d[\d,]+)",
    ],
    "Hashes Added": [
        r"(\d[\d,]+)\s*(?:new\s+)?hash(?:es)?",
    ],
    "Age 0-2 Victims": [
        r"(?:age[ds]?\s*)?(?:0\s*-\s*2|under\s*2|babies?).*?(\d[\d,]+)%?",
    ],
    "Domains Hosting CSAM": [
        r"(\d[\d,]+)\s*(?:unique\s+)?domains?",
    ],
}


class IWFReportsScraper(BasePDFReportScraper):
    """Scraper for Internet Watch Foundation annual reports.

    Downloads IWF annual report PDFs, extracts CSAM statistics
    from both tables and text, and normalizes into statistical_reports
    records.
    """

    name: str = "iwf_reports"
    source_url: str = (
        "https://www.iwf.org.uk/about-us/who-we-are/annual-reports/"
    )
    catalog_url: str = (
        "https://www.iwf.org.uk/about-us/who-we-are/annual-reports/"
    )
    schedule: str = "0 3 1 5 *"
    priority: str = "P1"
    rate_limit_delay: float = 3.0
    pdf_link_pattern: str = r"annual.*report.*\.pdf|\.pdf.*annual"

    def _extract_year(self, text: str) -> int | None:
        """Extract a report year from text or URL."""
        match = _YEAR_PATTERN.search(text)
        return int(match.group()) if match else None

    def _parse_numeric(self, text: str) -> float | None:
        """Parse a numeric string, stripping commas and whitespace."""
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None
        # Handle percentages
        cleaned = cleaned.rstrip("%")
        try:
            return float(cleaned) if "." in cleaned else float(int(cleaned))
        except ValueError:
            return None

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Convert IWF PDF tables into statistical_reports records.

        Extracts yearly CSAM statistics from tabular data in the
        annual reports.

        Args:
            tables: Raw tables from PDF extraction.
            pdf_url: Source URL for provenance.

        Returns:
            List of normalized statistical_reports records.
        """
        report_year = self._extract_year(pdf_url)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        for table in tables:
            if len(table) < 2:
                continue

            headers = table[0]
            # Look for year columns in headers
            year_cols: dict[int, int] = {}
            for i, header in enumerate(headers):
                year_match = _YEAR_PATTERN.search(header)
                if year_match:
                    year_cols[i] = int(year_match.group())

            for row in table[1:]:
                indicator = row[0].strip() if row and row[0] else ""
                if not indicator:
                    continue

                if year_cols:
                    # Extract value for each year column
                    for col_idx, year in year_cols.items():
                        if col_idx < len(row):
                            value = self._parse_numeric(row[col_idx])
                            if value is not None:
                                unit = self._infer_unit(indicator, row[col_idx])
                                records.append({
                                    "source_name": "IWF",
                                    "report_year": year,
                                    "report_title": "IWF Annual Report",
                                    "indicator": indicator,
                                    "value": value,
                                    "unit": unit,
                                    "geographic_scope": "Global",
                                    "pdf_url": pdf_url,
                                    "extraction_method": "pdfplumber_table",
                                    "scraped_at": now,
                                })
                else:
                    # No year columns — use second cell as value
                    if len(row) >= 2:
                        value = self._parse_numeric(row[1])
                        if value is not None:
                            unit = self._infer_unit(indicator, row[1])
                            records.append({
                                "source_name": "IWF",
                                "report_year": report_year,
                                "report_title": "IWF Annual Report",
                                "indicator": indicator,
                                "value": value,
                                "unit": unit,
                                "geographic_scope": "Global",
                                "pdf_url": pdf_url,
                                "extraction_method": "pdfplumber_table",
                                "scraped_at": now,
                            })

        return records

    @staticmethod
    def _infer_unit(indicator: str, raw_value: str) -> str:
        """Infer the unit of measurement from context."""
        indicator_lower = indicator.lower()
        if "%" in raw_value:
            return "percent"
        if "url" in indicator_lower or "webpage" in indicator_lower:
            return "URLs"
        if "report" in indicator_lower:
            return "reports"
        if "hash" in indicator_lower:
            return "hashes"
        if "domain" in indicator_lower:
            return "domains"
        if "image" in indicator_lower or "video" in indicator_lower:
            return "items"
        return "count"

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the IWF report scraping pipeline.

        Fetches the catalog page, discovers PDF links, downloads each
        report, and extracts statistics from tables and text.
        """
        url = self.catalog_url
        response = await self.fetch(url)
        pdf_urls = self.discover_pdf_urls(response.text)

        if not pdf_urls:
            logger.warning("[%s] No PDF URLs found at %s", self.name, url)
            return []

        logger.info("[%s] Discovered %d PDF report URLs", self.name, len(pdf_urls))

        all_records: list[dict[str, Any]] = []
        for pdf_url in pdf_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)

                # Try table extraction first
                tables = self.extract_tables(pdf_path)
                table_records = self.parse_tables(tables, pdf_url)

                if table_records:
                    all_records.extend(table_records)
                else:
                    # Fallback to text extraction
                    text_records = self._extract_from_text(pdf_path, pdf_url)
                    all_records.extend(text_records)
            except Exception as exc:
                logger.error("[%s] Failed to process %s: %s", self.name, pdf_url, exc)

        return all_records

    def _extract_from_text(
        self, pdf_path: Path, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Fallback extraction using regex patterns on PDF text."""
        text = self.extract_text(pdf_path)
        if not text:
            return []

        report_year = self._extract_year(pdf_url) or self._extract_year(text)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        for indicator_name, patterns in _IWF_METRICS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = self._parse_numeric(match.group(1))
                    if value is not None:
                        records.append({
                            "source_name": "IWF",
                            "report_year": report_year,
                            "report_title": "IWF Annual Report",
                            "indicator": indicator_name,
                            "value": value,
                            "unit": "count",
                            "geographic_scope": "Global",
                            "pdf_url": pdf_url,
                            "extraction_method": "text_regex",
                            "scraped_at": now,
                        })
                        break

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a statistical_reports record from IWF.

        Requires source_name, indicator, and either value or
        report_title.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
            and (record.get("value") is not None or record.get("report_title"))
        )
