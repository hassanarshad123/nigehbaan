"""Sahil 'Cruel Numbers' annual report scraper.

Wraps the existing SahilParser to discover, download, and parse Sahil's
annual 'Cruel Numbers' PDF reports tracking child abuse across Pakistan.

URL: https://sahil.org/cruel-numbers/
Schedule: Annually (0 0 1 1 *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from data.scrapers.base_pdf_scraper import BasePDFReportScraper
from data.parsers.sahil_parser import SahilParser

logger = logging.getLogger(__name__)


class SahilScraper(BasePDFReportScraper):
    """Scraper for Sahil 'Cruel Numbers' annual child abuse reports.

    Discovers PDF links from the Sahil catalog page, downloads each
    report, then delegates parsing to the existing SahilParser which
    handles table extraction, category normalization, and province
    normalization.
    """

    name: str = "sahil"
    source_url: str = "https://sahil.org/cruel-numbers/"
    catalog_url: str = "https://sahil.org/cruel-numbers/"
    schedule: str = "0 0 1 1 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    pdf_link_pattern: str = r"cruel.?numbers.*\.pdf|annual.*report.*\.pdf|sahil.*\d{4}.*\.pdf"

    def _extract_year_from_url(self, pdf_url: str) -> int | None:
        """Extract report year from a PDF URL or filename.

        Args:
            pdf_url: URL of the PDF file.

        Returns:
            Extracted year or None if not found.
        """
        year_match = re.search(r"20[0-2]\d", pdf_url)
        if year_match:
            return int(year_match.group())
        return None

    def _convert_to_statistical_record(
        self, parsed: dict[str, Any], year: int, pdf_url: str
    ) -> dict[str, Any]:
        """Convert a SahilParser record to the statistical_reports schema.

        Args:
            parsed: Record dict from SahilParser.parse_report().
            year: Report year.
            pdf_url: Source PDF URL for provenance.

        Returns:
            Record dict conforming to statistical_reports table schema.
        """
        indicator = parsed.get("crime_category", "")
        value = parsed.get("case_count", 0)
        province = parsed.get("province", "")
        gender = parsed.get("victim_gender", "")

        return {
            "source_name": self.name,
            "report_year": year,
            "report_title": f"Cruel Numbers {year}",
            "indicator": indicator,
            "value": value,
            "unit": "cases",
            "geographic_scope": province or "Pakistan",
            "victim_gender": gender or None,
            "victim_age_bracket": "0-18",
            "pdf_url": pdf_url,
            "extraction_method": "pdfplumber+sahil_parser",
            "extraction_confidence": 0.85,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch catalog page, discover PDFs, download and parse each.

        Uses SahilParser.parse_report() for extraction, then converts
        results to the standard statistical_reports format.

        Returns:
            List of statistical_reports records.
        """
        response = await self.fetch(self.catalog_url)
        pdf_urls = self.discover_pdf_urls(response.text)

        if not pdf_urls:
            logger.warning("[%s] No PDF URLs found at %s", self.name, self.catalog_url)
            return []

        logger.info("[%s] Discovered %d PDF links", self.name, len(pdf_urls))

        raw_dir = self.get_raw_dir()
        parser = SahilParser(reports_dir=raw_dir)
        all_records: list[dict[str, Any]] = []

        for pdf_url in pdf_urls:
            year = self._extract_year_from_url(pdf_url)
            if year is None:
                logger.warning("[%s] Could not determine year for %s, skipping", self.name, pdf_url)
                continue

            try:
                pdf_path = await self.download_pdf(pdf_url)
                parsed_records = parser.parse_report(pdf_path, year)

                for parsed in parsed_records:
                    record = self._convert_to_statistical_record(parsed, year, pdf_url)
                    all_records.append(record)

                logger.info(
                    "[%s] Parsed %d records from %s (year %d)",
                    self.name, len(parsed_records), pdf_path.name, year,
                )
            except Exception as exc:
                logger.error("[%s] Failed to process %s: %s", self.name, pdf_url, exc)

        logger.info("[%s] Total records extracted: %d", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Sahil statistical report record.

        Requires source_name and a non-empty indicator.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
        )
