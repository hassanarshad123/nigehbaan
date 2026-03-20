"""Pahchaan hospital-based child protection data scraper.

Scrapes Pahchaan (pahchaan.info) for hospital-based child protection
data spanning 10+ years. Pahchaan maintains records of child abuse
cases reported through hospital networks across Pakistan.

URL: https://pahchaan.info
Schedule: Quarterly (0 3 1 */3 *)
Priority: P2
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

# Expected indicators in Pahchaan reports
PAHCHAAN_INDICATORS: list[str] = [
    "physical_abuse",
    "sexual_abuse",
    "emotional_abuse",
    "neglect",
    "child_labor",
    "child_marriage",
    "abandonment",
    "trafficking",
    "hospital_referrals",
    "cases_registered",
    "cases_resolved",
    "children_rehabilitated",
]


class PahchaanScraper(BasePDFReportScraper):
    """Scraper for Pahchaan hospital-based child protection data.

    Pahchaan collects child abuse data through hospital-based child
    protection units, providing medical-sourced evidence of abuse
    categories, age distributions, and geographic patterns.
    """

    name: str = "pahchaan"
    source_url: str = "https://pahchaan.info"
    catalog_url: str = "https://pahchaan.info"
    schedule: str = "0 3 1 */3 *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0

    pdf_link_pattern: str = r"\.pdf"

    # Additional pages to check for reports and data
    REPORT_PAGES: list[str] = [
        "https://pahchaan.info/reports",
        "https://pahchaan.info/publications",
        "https://pahchaan.info/data",
        "https://pahchaan.info/resources",
    ]

    def _classify_indicator(self, text: str) -> str:
        """Map free-text descriptions to standardized indicators.

        Args:
            text: Raw text from table cell or heading.

        Returns:
            Standardized indicator name.
        """
        text_lower = text.lower()

        mapping: dict[str, list[str]] = {
            "physical_abuse": ["physical abuse", "physical violence", "beating", "torture"],
            "sexual_abuse": ["sexual abuse", "rape", "sodomy", "molestation", "csa"],
            "emotional_abuse": ["emotional", "psychological", "mental abuse"],
            "neglect": ["neglect", "negligence", "failure to provide"],
            "child_labor": ["child lab", "labor", "labour", "working child"],
            "child_marriage": ["child marriage", "early marriage"],
            "abandonment": ["abandon", "abandoned", "left behind"],
            "trafficking": ["trafficking", "traffick", "smuggling"],
            "hospital_referrals": ["referral", "hospital", "medical"],
            "cases_registered": ["registered", "reported", "filed"],
            "cases_resolved": ["resolved", "closed", "completed"],
            "children_rehabilitated": ["rehabilitat", "recovery", "reintegrat"],
        }

        for indicator, keywords in mapping.items():
            if any(kw in text_lower for kw in keywords):
                return indicator

        return text.strip()[:100]

    def _extract_year_from_context(self, pdf_url: str) -> int | None:
        """Extract year from PDF URL or filename.

        Args:
            pdf_url: URL of the PDF.

        Returns:
            Year or None if not determinable.
        """
        year_match = re.search(r"20[0-2]\d", pdf_url)
        if year_match:
            return int(year_match.group())
        return None

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Parse extracted PDF tables into statistical_reports records.

        Handles hospital-based child protection data tables with
        categories for abuse types, geographic breakdowns, and
        age/gender distributions.

        Args:
            tables: Raw tables from PDF extraction.
            pdf_url: Source PDF URL for provenance.

        Returns:
            List of statistical_reports records.
        """
        year = self._extract_year_from_context(pdf_url) or datetime.now(timezone.utc).year
        records: list[dict[str, Any]] = []

        for table in tables:
            if len(table) < 2:
                continue

            headers = [h.strip().lower() if h else "" for h in table[0]]

            # Detect gender columns
            has_male = any("male" in h or "boy" in h for h in headers)
            has_female = any("female" in h or "girl" in h for h in headers)

            for row in table[1:]:
                if not row or all(not cell.strip() for cell in row if cell):
                    continue

                # First cell is typically the indicator/category
                indicator_text = row[0].strip() if row[0] else ""
                if not indicator_text:
                    continue

                indicator = self._classify_indicator(indicator_text)

                # Extract values — handle gendered columns
                if has_male and has_female:
                    for i, header in enumerate(headers):
                        if i >= len(row):
                            break
                        cell = row[i].strip() if row[i] else ""
                        value = self._parse_numeric(cell)
                        if value is None:
                            continue

                        gender = None
                        if "male" in header or "boy" in header:
                            gender = "male"
                        elif "female" in header or "girl" in header:
                            gender = "female"
                        elif "total" in header:
                            gender = None
                        else:
                            continue

                        records.append(self._build_record(
                            indicator=indicator,
                            value=value,
                            year=year,
                            pdf_url=pdf_url,
                            gender=gender,
                        ))
                else:
                    # Single value row — extract last numeric cell
                    value = self._extract_last_numeric(row)
                    if value is not None:
                        records.append(self._build_record(
                            indicator=indicator,
                            value=value,
                            year=year,
                            pdf_url=pdf_url,
                        ))

        return records

    def _build_record(
        self,
        indicator: str,
        value: int | float,
        year: int,
        pdf_url: str,
        gender: str | None = None,
        province: str = "Pakistan",
    ) -> dict[str, Any]:
        """Build a single statistical_reports record.

        Args:
            indicator: Standardized indicator name.
            value: Numeric value.
            year: Report year.
            pdf_url: Source URL.
            gender: Optional victim gender.
            province: Geographic scope.

        Returns:
            Record dict for statistical_reports table.
        """
        return {
            "source_name": self.name,
            "report_year": year,
            "report_title": f"Pahchaan Hospital-Based Child Protection Report {year}",
            "indicator": indicator,
            "value": value,
            "unit": "cases",
            "geographic_scope": province,
            "victim_gender": gender,
            "victim_age_bracket": "0-18",
            "pdf_url": pdf_url,
            "extraction_method": "pdfplumber",
            "extraction_confidence": 0.75,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    def _parse_numeric(self, text: str) -> int | float | None:
        """Parse a string as a numeric value.

        Args:
            text: Raw cell text.

        Returns:
            Parsed number or None.
        """
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None
        try:
            if "." in cleaned:
                return float(cleaned)
            return int(cleaned)
        except ValueError:
            return None

    def _extract_last_numeric(self, row: list[str]) -> int | float | None:
        """Extract the last numeric value from a table row.

        Args:
            row: List of cell strings.

        Returns:
            Last numeric value found, or None.
        """
        for cell in reversed(row):
            value = self._parse_numeric(cell or "")
            if value is not None:
                return value
        return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch Pahchaan pages, discover PDFs, download and extract data.

        Checks the main page and known report sub-pages for PDF links.

        Returns:
            List of statistical_reports records.
        """
        all_pdf_urls: list[str] = []

        # Check main page
        try:
            response = await self.fetch(self.source_url)
            pdf_urls = self.discover_pdf_urls(response.text)
            all_pdf_urls.extend(pdf_urls)
        except Exception as exc:
            logger.warning("[%s] Failed to fetch main page: %s", self.name, exc)

        # Check known report sub-pages
        for page_url in self.REPORT_PAGES:
            try:
                response = await self.fetch(page_url)
                pdf_urls = self.discover_pdf_urls(response.text)
                all_pdf_urls.extend(pdf_urls)
            except Exception as exc:
                logger.warning("[%s] Failed to fetch %s: %s", self.name, page_url, exc)

        # Deduplicate
        seen: set[str] = set()
        unique_urls: list[str] = []
        for url in all_pdf_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        if not unique_urls:
            logger.warning("[%s] No PDF URLs found across all pages", self.name)
            return []

        logger.info("[%s] Discovered %d unique PDF links", self.name, len(unique_urls))

        all_records: list[dict[str, Any]] = []
        for pdf_url in unique_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)
                tables = self.extract_tables(pdf_path)
                records = self.parse_tables(tables, pdf_url)
                all_records.extend(records)
                logger.info("[%s] Extracted %d records from %s", self.name, len(records), pdf_url)
            except Exception as exc:
                logger.error("[%s] Failed to process %s: %s", self.name, pdf_url, exc)

        logger.info("[%s] Total records: %d", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Pahchaan statistical report record.

        Requires source_name and a non-empty indicator.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
        )
