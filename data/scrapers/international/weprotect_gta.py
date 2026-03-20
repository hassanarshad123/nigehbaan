"""WeProtect Global Alliance — Global Threat Assessment scraper.

Scrapes the WeProtect Global Threat Assessment reports which provide
comprehensive analysis of online child sexual exploitation and abuse
trends worldwide.

URL: https://www.weprotect.org/global-threat-assessment/
Schedule: Biennial — every 2 years (0 3 1 1 *)
Priority: P2
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

# Key indicators tracked in the Global Threat Assessment
_GTA_INDICATORS: dict[str, list[str]] = {
    "CSAM Reports to NCMEC": [
        r"(\d[\d,]*(?:\.\d+)?)\s*(?:million\s+)?(?:reports?\s+)?(?:to\s+)?(?:NCMEC|CyberTipline)",
        r"(?:NCMEC|CyberTipline).*?(\d[\d,]*(?:\.\d+)?)\s*million",
    ],
    "Online Grooming Offences": [
        r"(\d[\d,]*)\s*(?:online\s+)?grooming\s*(?:offences?|incidents?|cases?)",
        r"grooming.*?(\d[\d,]*)\s*(?:offences?|incidents?|cases?)",
    ],
    "Self-Generated CSAM": [
        r"(\d[\d,]*)\s*%?\s*self[- ]generated",
        r"self[- ]generated.*?(\d[\d,]*)\s*%",
    ],
    "Live-Streamed Abuse": [
        r"(\d[\d,]*)\s*(?:%\s+)?live[- ]stream",
        r"live[- ]stream.*?(\d[\d,]*)",
    ],
    "Children at Risk Online": [
        r"(\d[\d,]*(?:\.\d+)?)\s*(?:million\s+)?children.*?(?:at\s+risk|vulnerable|exposed)",
    ],
    "Financial Sextortion Cases": [
        r"(\d[\d,]*)\s*(?:financial\s+)?sextortion",
        r"sextortion.*?(\d[\d,]*)",
    ],
    "Countries Assessed": [
        r"(\d[\d,]*)\s*countries?\s*(?:assessed|reviewed|analysed)",
    ],
    "Pakistan-Specific Findings": [
        r"Pakistan.*?(\d[\d,]*(?:\.\d+)?)\s*(?:million|%|cases?|reports?|victims?)",
    ],
    "Age 0-10 Victims": [
        r"(?:age[ds]?\s*)?(?:0\s*-\s*10|under\s*10|younger).*?(\d[\d,]*)%?",
    ],
    "Darknet CSAM Sites": [
        r"(\d[\d,]*)\s*(?:darknet|dark\s*web)\s*(?:sites?|platforms?|forums?)",
    ],
}


class WeProtectGTAScraper(BasePDFReportScraper):
    """Scraper for WeProtect Global Threat Assessment reports.

    Downloads GTA PDF reports, extracts tables and key statistics
    on global online child sexual exploitation trends. The GTA is
    published roughly every 2 years and is a key reference for the
    scale and nature of the threat.
    """

    name: str = "weprotect_gta"
    source_url: str = "https://www.weprotect.org/global-threat-assessment/"
    catalog_url: str = "https://www.weprotect.org/global-threat-assessment/"
    schedule: str = "0 3 1 1 *"
    priority: str = "P2"
    rate_limit_delay: float = 3.0
    pdf_link_pattern: str = r"threat.*assessment.*\.pdf|gta.*\.pdf|\.pdf"

    def _extract_year(self, text: str) -> int | None:
        """Extract a report year from text or URL."""
        match = _YEAR_PATTERN.search(text)
        return int(match.group()) if match else None

    def _parse_numeric(self, text: str) -> float | None:
        """Parse a numeric value, handling commas and magnitude words."""
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None
        if cleaned.endswith("%"):
            try:
                return float(cleaned[:-1])
            except ValueError:
                return None
        # Handle "million", "billion" suffixes
        magnitude_map = {
            "million": 1_000_000,
            "billion": 1_000_000_000,
            "thousand": 1_000,
        }
        for word, multiplier in magnitude_map.items():
            if word in text.lower():
                nums = _NUMBER_PATTERN.findall(text)
                if nums:
                    try:
                        return float(nums[0].replace(",", "")) * multiplier
                    except ValueError:
                        pass
        try:
            return float(cleaned) if "." in cleaned else float(int(cleaned))
        except ValueError:
            return None

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Convert GTA PDF tables into statistical_reports records.

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
            for row in table[1:]:
                # First non-empty cell is the indicator
                indicator = ""
                for cell in row:
                    if cell and cell.strip():
                        indicator = cell.strip()
                        break

                if not indicator:
                    continue

                # Extract numeric values from remaining cells
                for i, cell in enumerate(row):
                    if not cell:
                        continue
                    value = self._parse_numeric(cell)
                    if value is not None:
                        # Use header if available for context
                        column_header = headers[i] if i < len(headers) else ""
                        full_indicator = (
                            f"{indicator} ({column_header})"
                            if column_header and column_header != indicator
                            else indicator
                        )

                        geographic_scope = "Global"
                        if "pakistan" in indicator.lower():
                            geographic_scope = "Pakistan"

                        unit = "percent" if "%" in cell else "count"

                        records.append({
                            "source_name": "WeProtect Global Alliance",
                            "report_year": report_year,
                            "report_title": "Global Threat Assessment",
                            "indicator": full_indicator,
                            "value": value,
                            "unit": unit,
                            "geographic_scope": geographic_scope,
                            "pdf_url": pdf_url,
                            "extraction_method": "pdfplumber_table",
                            "scraped_at": now,
                        })

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the WeProtect GTA scraping pipeline.

        Fetches the catalog page, discovers GTA PDF links, downloads
        each report, and extracts statistics from tables and text.
        """
        url = self.catalog_url
        response = await self.fetch(url)
        pdf_urls = self.discover_pdf_urls(response.text)

        if not pdf_urls:
            logger.warning("[%s] No PDF URLs found at %s", self.name, url)
            # Try alternative: look for download buttons / links
            pdf_urls = self._discover_alternative_links(response.text)

        if not pdf_urls:
            logger.warning("[%s] No GTA reports found", self.name)
            return []

        logger.info("[%s] Discovered %d PDF URLs", self.name, len(pdf_urls))

        all_records: list[dict[str, Any]] = []
        for pdf_url in pdf_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)

                # Try table extraction
                tables = self.extract_tables(pdf_path)
                table_records = self.parse_tables(tables, pdf_url)

                if table_records:
                    all_records.extend(table_records)

                # Always also try text extraction for key metrics
                text_records = self._extract_from_text(pdf_path, pdf_url)
                # Only add text records for indicators not already captured
                existing_indicators = {r["indicator"] for r in table_records}
                for tr in text_records:
                    if tr["indicator"] not in existing_indicators:
                        all_records.append(tr)
            except Exception as exc:
                logger.error(
                    "[%s] Failed to process %s: %s", self.name, pdf_url, exc
                )

        return all_records

    def _discover_alternative_links(self, html: str) -> list[str]:
        """Find GTA download links that may not match the PDF pattern."""
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse

        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True).lower()
            if any(kw in text for kw in ["download", "read", "assessment", "report"]):
                if href.endswith(".pdf") or "pdf" in href.lower():
                    if href.startswith("http"):
                        urls.append(href)
                    elif href.startswith("/"):
                        parsed = urlparse(self.source_url)
                        urls.append(f"{parsed.scheme}://{parsed.netloc}{href}")

        return urls

    def _extract_from_text(
        self, pdf_path: Path, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Extract key GTA metrics from PDF text using regex patterns."""
        text = self.extract_text(pdf_path)
        if not text:
            return []

        report_year = self._extract_year(pdf_url) or self._extract_year(text)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        for indicator_name, patterns in _GTA_INDICATORS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    raw_value = match.group(1)
                    # Check for "million" in surrounding context
                    context_start = max(0, match.start() - 20)
                    context_end = min(len(text), match.end() + 30)
                    context = text[context_start:context_end]

                    value = self._parse_numeric(context) or self._parse_numeric(raw_value)
                    if value is not None:
                        geographic_scope = (
                            "Pakistan"
                            if "pakistan" in indicator_name.lower()
                            else "Global"
                        )
                        unit = "percent" if "%" in context else "count"

                        records.append({
                            "source_name": "WeProtect Global Alliance",
                            "report_year": report_year,
                            "report_title": "Global Threat Assessment",
                            "indicator": indicator_name,
                            "value": value,
                            "unit": unit,
                            "geographic_scope": geographic_scope,
                            "pdf_url": pdf_url,
                            "extraction_method": "text_regex",
                            "scraped_at": now,
                        })
                        break

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a statistical_reports record from WeProtect GTA.

        Requires source_name, indicator, and either a value or
        report_title.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
            and (record.get("value") is not None or record.get("report_title"))
        )
