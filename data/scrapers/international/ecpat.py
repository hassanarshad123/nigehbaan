"""ECPAT International Pakistan country assessment scraper.

Scrapes ECPAT's Pakistan country page for country assessment PDFs
and Global Boys Initiative (GBI) survey data related to child sexual
exploitation.

URL: https://ecpat.org/country/pakistan/
Schedule: Every 3 years — rarely updated (0 0 1 1 */3)
Priority: P2
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

# Indicators expected in ECPAT country assessment reports
ECPAT_INDICATORS: list[str] = [
    "online_child_sexual_exploitation",
    "child_sexual_abuse_material",
    "child_trafficking_sexual_exploitation",
    "child_prostitution",
    "child_marriage_sexual_exploitation",
    "sexual_exploitation_travel_tourism",
    "gbi_survey_prevalence",
    "gbi_survey_awareness",
    "legislation_compliance",
    "national_response_rating",
]


class ECPATScraper(BasePDFReportScraper):
    """Scraper for ECPAT country assessment and GBI data on Pakistan.

    Downloads country assessment PDFs and extracts structured data
    on child sexual exploitation indicators, legal framework compliance,
    and GBI survey results.
    """

    name: str = "ecpat"
    source_url: str = "https://ecpat.org/country/pakistan/"
    catalog_url: str = "https://ecpat.org/country/pakistan/"
    schedule: str = "0 0 1 1 */3"
    priority: str = "P2"
    rate_limit_delay: float = 2.0

    pdf_link_pattern: str = r"pakistan.*\.pdf|country.*profile.*\.pdf|assessment.*\.pdf|gbi.*\.pdf"

    def _extract_year_from_context(self, pdf_url: str, text: str = "") -> int | None:
        """Extract report year from URL or surrounding text.

        Args:
            pdf_url: URL of the PDF.
            text: Optional surrounding text context.

        Returns:
            Report year or None.
        """
        combined = f"{pdf_url} {text}"
        year_match = re.search(r"20[0-2]\d", combined)
        if year_match:
            return int(year_match.group())
        return None

    def _classify_indicator(self, row_text: str) -> str:
        """Classify a table row into a known ECPAT indicator.

        Args:
            row_text: Combined text from a table row.

        Returns:
            Matched indicator name or the original text as fallback.
        """
        text_lower = row_text.lower()

        indicator_keywords: dict[str, list[str]] = {
            "online_child_sexual_exploitation": ["online", "csam", "ict", "internet"],
            "child_sexual_abuse_material": ["csam", "pornograph", "material"],
            "child_trafficking_sexual_exploitation": ["trafficking", "traffick"],
            "child_prostitution": ["prostitut", "commercial sex"],
            "child_marriage_sexual_exploitation": ["marriage", "early marriage"],
            "sexual_exploitation_travel_tourism": ["travel", "tourism"],
            "gbi_survey_prevalence": ["gbi", "boys", "prevalence"],
            "gbi_survey_awareness": ["gbi", "awareness", "knowledge"],
            "legislation_compliance": ["legislat", "law", "legal", "compliance"],
            "national_response_rating": ["response", "rating", "national plan"],
        }

        for indicator, keywords in indicator_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return indicator

        return row_text.strip()[:100]

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Parse extracted PDF tables into statistical_reports records.

        Handles both country assessment tables and GBI survey data tables.

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

            for row in table[1:]:
                if not row or all(not cell.strip() for cell in row if cell):
                    continue

                row_text = " ".join(cell for cell in row if cell)
                indicator = self._classify_indicator(row_text)

                # Extract numeric value from the row
                value = self._extract_value(row)

                records.append({
                    "source_name": self.name,
                    "report_year": year,
                    "report_title": f"ECPAT Country Assessment - Pakistan {year}",
                    "indicator": indicator,
                    "value": value,
                    "unit": "assessment_score" if value and isinstance(value, float) else "cases",
                    "geographic_scope": "Pakistan",
                    "victim_gender": None,
                    "victim_age_bracket": "0-18",
                    "pdf_url": pdf_url,
                    "extraction_method": "pdfplumber",
                    "extraction_confidence": 0.7,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })

        return records

    def _extract_value(self, row: list[str]) -> float | int | None:
        """Extract the first numeric value from a table row.

        Args:
            row: List of cell strings from a table row.

        Returns:
            Extracted numeric value or None.
        """
        for cell in reversed(row):
            if not cell:
                continue
            cleaned = cell.strip().replace(",", "").replace("%", "")
            try:
                if "." in cleaned:
                    return float(cleaned)
                return int(cleaned)
            except ValueError:
                continue
        return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch ECPAT Pakistan page, discover PDFs, extract data.

        Also attempts to extract inline HTML data from the country
        page itself (e.g., key statistics displayed in the page body).

        Returns:
            List of statistical_reports records.
        """
        response = await self.fetch(self.catalog_url)
        html = response.text

        # Discover and process PDFs
        pdf_urls = self.discover_pdf_urls(html)
        logger.info("[%s] Discovered %d PDF links", self.name, len(pdf_urls))

        all_records: list[dict[str, Any]] = []

        for pdf_url in pdf_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)
                tables = self.extract_tables(pdf_path)
                records = self.parse_tables(tables, pdf_url)
                all_records.extend(records)
                logger.info("[%s] Extracted %d records from %s", self.name, len(records), pdf_url)
            except Exception as exc:
                logger.error("[%s] Failed to process %s: %s", self.name, pdf_url, exc)

        # Also extract inline page statistics
        try:
            inline_records = self._extract_inline_stats(html)
            all_records.extend(inline_records)
        except Exception as exc:
            logger.warning("[%s] Inline stats extraction failed: %s", self.name, exc)

        logger.info("[%s] Total records: %d", self.name, len(all_records))
        return all_records

    def _extract_inline_stats(self, html: str) -> list[dict[str, Any]]:
        """Extract key statistics displayed inline on the ECPAT page.

        Args:
            html: Raw HTML of the country page.

        Returns:
            List of statistical_reports records from inline content.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        records: list[dict[str, Any]] = []

        # Look for stat blocks with numbers
        for block in soup.find_all(["div", "section", "p"]):
            text = block.get_text(strip=True)
            if not text or len(text) > 500:
                continue

            # Match patterns like "X% of children" or "X,XXX cases"
            stat_match = re.search(
                r"(\d[\d,.]*)\s*(%?)\s*(children|child|boys|girls|victims|cases)",
                text,
                re.IGNORECASE,
            )
            if stat_match:
                raw_value = stat_match.group(1).replace(",", "")
                unit = "percent" if stat_match.group(2) == "%" else "count"
                try:
                    value = float(raw_value) if "." in raw_value else int(raw_value)
                except ValueError:
                    continue

                records.append({
                    "source_name": self.name,
                    "report_year": datetime.now(timezone.utc).year,
                    "report_title": "ECPAT Pakistan Country Page - Inline Stats",
                    "indicator": text[:200],
                    "value": value,
                    "unit": unit,
                    "geographic_scope": "Pakistan",
                    "victim_gender": None,
                    "victim_age_bracket": "0-18",
                    "pdf_url": self.source_url,
                    "extraction_method": "html_inline",
                    "extraction_confidence": 0.6,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an ECPAT statistical report record.

        Requires source_name and either an indicator or report_title.
        """
        return bool(
            record.get("source_name")
            and (record.get("indicator") or record.get("report_title"))
        )
