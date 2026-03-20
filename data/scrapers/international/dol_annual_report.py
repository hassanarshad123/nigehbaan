"""US Department of Labor annual child labor report scraper (PDF extraction).

Downloads and extracts tables from the DOL Bureau of International Labor
Affairs (ILAB) annual report on the worst forms of child labor in Pakistan.
This is the most comprehensive annual assessment of child labor conditions,
covering sectoral prevalence, legislation, and enforcement.

Source: https://www.dol.gov/agencies/ilab/resources/reports/child-labor/pakistan
Schedule: Annually (0 3 15 10 *)
Priority: P1 — Most comprehensive annual child labor report
"""

from datetime import datetime, timezone
from typing import Any

import logging
import re

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

# Keywords that identify child-labor-relevant tables within the PDF
_TABLE_KEYWORDS: list[str] = [
    "worst forms",
    "child labor",
    "hazardous",
    "sector",
    "agriculture",
    "manufacturing",
    "industry",
    "services",
    "brick kiln",
    "carpet",
    "bonded",
    "domestic",
    "mining",
    "prevalence",
    "enforcement",
    "inspections",
]


class DOLAnnualReportScraper(BasePDFReportScraper):
    """Scraper for DOL ILAB annual child labor findings for Pakistan.

    Discovers PDF report links on the Pakistan country page, downloads
    the latest annual report, extracts tables about worst forms of
    child labor, and maps rows to statistical_reports records.
    """

    name: str = "dol_annual_report"
    source_url: str = (
        "https://www.dol.gov/agencies/ilab/resources/reports/"
        "child-labor/pakistan"
    )
    catalog_url: str = (
        "https://www.dol.gov/agencies/ilab/resources/reports/"
        "child-labor/pakistan"
    )
    schedule: str = "0 3 15 10 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0
    pdf_link_pattern: str = r"pakistan.*\.pdf|findings.*\.pdf|child.*labor.*\.pdf"

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch catalog page, discover PDFs, download, and extract tables."""
        logger.info("[%s] Fetching catalog page: %s", self.name, self.catalog_url)
        response = await self.fetch(self.catalog_url)
        pdf_urls = self.discover_pdf_urls(response.text)

        # Also check for direct links that may not match the PDF pattern
        pdf_urls = self._augment_with_findings_links(response.text, pdf_urls)

        if not pdf_urls:
            logger.warning("[%s] No PDF URLs found on catalog page", self.name)
            return []

        logger.info("[%s] Found %d PDF URLs", self.name, len(pdf_urls))

        all_records: list[dict[str, Any]] = []
        for pdf_url in pdf_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)
                tables = self.extract_tables(pdf_path)
                text = self.extract_text(pdf_path)
                records = self.parse_tables(tables, pdf_url)

                # If table extraction yields nothing, fall back to text
                if not records and text:
                    records = self._extract_from_text(text, pdf_url)

                all_records.extend(records)
            except Exception as exc:
                logger.error(
                    "[%s] Failed to process %s: %s", self.name, pdf_url, exc
                )

        return all_records

    def _augment_with_findings_links(
        self, html: str, existing: list[str]
    ) -> list[str]:
        """Find additional PDF links via broader patterns."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        existing_set = set(existing)

        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True).lower()
            if ".pdf" in href.lower() and (
                "finding" in text or "pakistan" in text or "child labor" in text
            ):
                full_url = (
                    href if href.startswith("http")
                    else f"https://www.dol.gov{href}"
                )
                if full_url not in existing_set:
                    existing.append(full_url)
                    existing_set.add(full_url)

        return existing

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Parse extracted PDF tables into statistical_reports records.

        Identifies child-labor-relevant tables by scanning header/cell
        content for known keywords, then maps each data row to a record.
        """
        records: list[dict[str, Any]] = []
        year = self._extract_year(pdf_url)

        for table in tables:
            if not table or len(table) < 2:
                continue

            headers = [str(cell).strip().lower() for cell in table[0]]
            header_text = " ".join(headers)

            # Skip tables that are clearly not child-labor-relevant
            if not any(kw in header_text for kw in _TABLE_KEYWORDS):
                # Check a few data rows as well
                sample_text = " ".join(
                    str(cell).lower()
                    for row in table[1:4]
                    for cell in row
                )
                if not any(kw in sample_text for kw in _TABLE_KEYWORDS):
                    continue

            for row in table[1:]:
                cells = [str(cell).strip() for cell in row]
                if not any(cells):
                    continue

                indicator = cells[0] if cells else ""
                value_str = cells[1] if len(cells) > 1 else ""
                unit = cells[2] if len(cells) > 2 else ""

                value = self._parse_numeric(value_str)

                records.append({
                    "source_name": self.name,
                    "report_year": year,
                    "report_title": f"DOL Findings on the Worst Forms of Child Labor — Pakistan {year}",
                    "indicator": indicator,
                    "value": value,
                    "unit": unit or "count",
                    "geographic_scope": "Pakistan",
                    "pdf_url": pdf_url,
                    "extraction_method": "pdf_table_pdfplumber",
                    "extraction_confidence": 0.75,
                    "victim_gender": None,
                    "victim_age_bracket": None,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })

        return records

    def _extract_from_text(
        self, text: str, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Fallback: extract key statistics from raw PDF text using regex."""
        records: list[dict[str, Any]] = []
        year = self._extract_year(pdf_url)

        # Pattern: "X% of children" or "X million children"
        pct_pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:children|child)",
            re.IGNORECASE,
        )
        count_pattern = re.compile(
            r"(\d[\d,]*(?:\.\d+)?)\s*(?:million|thousand)?\s*(?:children|child)",
            re.IGNORECASE,
        )

        for match in pct_pattern.finditer(text):
            start = max(0, match.start() - 100)
            context = text[start:match.end() + 50]
            records.append({
                "source_name": self.name,
                "report_year": year,
                "report_title": f"DOL Findings — Pakistan {year}",
                "indicator": f"child_labor_text_extract: {context.strip()[:120]}",
                "value": float(match.group(1)),
                "unit": "percent",
                "geographic_scope": "Pakistan",
                "pdf_url": pdf_url,
                "extraction_method": "pdf_text_regex",
                "extraction_confidence": 0.50,
                "victim_gender": None,
                "victim_age_bracket": None,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })

        for match in count_pattern.finditer(text):
            start = max(0, match.start() - 100)
            context = text[start:match.end() + 50]
            value_str = match.group(1).replace(",", "")
            records.append({
                "source_name": self.name,
                "report_year": year,
                "report_title": f"DOL Findings — Pakistan {year}",
                "indicator": f"child_labor_count_extract: {context.strip()[:120]}",
                "value": float(value_str),
                "unit": "count",
                "geographic_scope": "Pakistan",
                "pdf_url": pdf_url,
                "extraction_method": "pdf_text_regex",
                "extraction_confidence": 0.40,
                "victim_gender": None,
                "victim_age_bracket": None,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })

        return records

    @staticmethod
    def _extract_year(url_or_text: str) -> str:
        """Extract a 4-digit year from a URL or text string."""
        match = re.search(r"20[0-2]\d", url_or_text)
        return match.group() if match else str(datetime.now(timezone.utc).year)

    @staticmethod
    def _parse_numeric(value_str: str) -> float | None:
        """Parse a numeric string, stripping commas and whitespace."""
        cleaned = value_str.replace(",", "").replace(" ", "").strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a DOL annual report record."""
        if not record.get("source_name"):
            return False
        if not record.get("indicator") and not record.get("report_title"):
            return False
        if not record.get("report_year"):
            return False
        return True
