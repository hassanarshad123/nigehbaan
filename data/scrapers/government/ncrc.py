"""NCRC (National Commission on the Rights of the Child) scraper.

Scrapes ncrc.gov.pk for the State of Children Report, street children
policy data, and other child rights publications.

URL: https://ncrc.gov.pk
Schedule: Annually (0 0 15 3 *)
Priority: P2
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

# Expected indicators in NCRC reports
NCRC_INDICATORS: list[str] = [
    "child_protection_cases",
    "child_labor",
    "child_marriage",
    "street_children",
    "juvenile_justice",
    "birth_registration",
    "child_trafficking",
    "child_sexual_abuse",
    "child_mortality",
    "education_access",
    "health_access",
    "child_poverty",
    "violence_against_children",
    "institutional_care",
    "alternative_care",
    "child_disability",
]


class NCRCScraper(BasePDFReportScraper):
    """Scraper for NCRC publications and child rights data.

    Targets the State of Children Report 2024, street children policy
    documents, and other NCRC publications containing statistical
    data on child rights in Pakistan.
    """

    name: str = "ncrc"
    source_url: str = "https://ncrc.gov.pk"
    catalog_url: str = "https://ncrc.gov.pk"
    schedule: str = "0 0 15 3 *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0

    pdf_link_pattern: str = r"\.pdf"

    # Known NCRC sub-pages that may host reports
    REPORT_PAGES: list[str] = [
        "https://ncrc.gov.pk/publications",
        "https://ncrc.gov.pk/reports",
        "https://ncrc.gov.pk/resources",
        "https://ncrc.gov.pk/state-of-children",
        "https://ncrc.gov.pk/policy-briefs",
    ]

    def _classify_indicator(self, text: str) -> str:
        """Map raw text to a standardized NCRC indicator.

        Args:
            text: Raw text from table cell or heading.

        Returns:
            Standardized indicator name.
        """
        text_lower = text.lower()

        mapping: dict[str, list[str]] = {
            "child_protection_cases": ["protection case", "child protection", "cpwb"],
            "child_labor": ["child lab", "labour", "labor", "working child"],
            "child_marriage": ["child marriage", "early marriage", "underage marriage"],
            "street_children": ["street child", "homeless child", "runaway"],
            "juvenile_justice": ["juvenile", "justice for child", "diversion", "jjsa"],
            "birth_registration": ["birth registr", "registered", "nadra"],
            "child_trafficking": ["trafficking", "traffick", "smuggling"],
            "child_sexual_abuse": ["sexual abuse", "rape", "sodomy", "csa"],
            "child_mortality": ["mortality", "death", "neonatal", "infant"],
            "education_access": ["education", "school", "enrolment", "out of school"],
            "health_access": ["health", "nutrition", "stunting", "wasting"],
            "child_poverty": ["poverty", "deprivation", "mpi"],
            "violence_against_children": ["violence", "physical abuse", "domestic violence"],
            "institutional_care": ["institutional", "shelter", "orphanage"],
            "alternative_care": ["alternative care", "foster", "kinship"],
            "child_disability": ["disability", "disabled", "special needs"],
        }

        for indicator, keywords in mapping.items():
            if any(kw in text_lower for kw in keywords):
                return indicator

        return text.strip()[:100]

    def _detect_province(self, row: list[str], headers: list[str]) -> str | None:
        """Detect province from a table row.

        Args:
            row: Table row cells.
            headers: Table header names.

        Returns:
            Province name or None.
        """
        province_map: dict[str, str] = {
            "punjab": "Punjab",
            "sindh": "Sindh",
            "kp": "Khyber Pakhtunkhwa",
            "kpk": "Khyber Pakhtunkhwa",
            "khyber pakhtunkhwa": "Khyber Pakhtunkhwa",
            "balochistan": "Balochistan",
            "ict": "Islamabad Capital Territory",
            "islamabad": "Islamabad Capital Territory",
            "ajk": "Azad Jammu & Kashmir",
            "gb": "Gilgit-Baltistan",
        }

        for i, header in enumerate(headers):
            if "province" in header or "region" in header or "area" in header:
                if i < len(row):
                    raw = row[i].strip().lower()
                    return province_map.get(raw, row[i].strip())

        # Also check cell content for province names
        for cell in row:
            if cell:
                cell_lower = cell.strip().lower()
                if cell_lower in province_map:
                    return province_map[cell_lower]

        return None

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Parse extracted PDF tables into statistical_reports records.

        Handles State of Children Report tables, street children data,
        and policy-related statistics.

        Args:
            tables: Raw tables from PDF extraction.
            pdf_url: Source PDF URL.

        Returns:
            List of statistical_reports records.
        """
        year = self._extract_year(pdf_url) or datetime.now(timezone.utc).year
        records: list[dict[str, Any]] = []

        for table in tables:
            if len(table) < 2:
                continue

            headers = [h.strip().lower() if h else "" for h in table[0]]

            for row in table[1:]:
                if not row or all(not cell.strip() for cell in row if cell):
                    continue

                indicator_text = row[0].strip() if row[0] else ""
                if not indicator_text:
                    continue

                indicator = self._classify_indicator(indicator_text)
                province = self._detect_province(row, headers)

                # Extract numeric values from the row
                for i in range(1, len(row)):
                    if i >= len(row):
                        break
                    cell = row[i].strip() if row[i] else ""
                    value = self._parse_numeric(cell)
                    if value is None:
                        continue

                    unit = "percent" if "%" in cell else "count"

                    # Detect gender from header
                    gender = None
                    if i < len(headers):
                        header = headers[i]
                        if "male" in header or "boy" in header:
                            gender = "male"
                        elif "female" in header or "girl" in header:
                            gender = "female"

                    report_title = "State of Children Report"
                    if "street" in pdf_url.lower() or "street" in indicator_text.lower():
                        report_title = "NCRC Street Children Policy Report"
                    elif "policy" in pdf_url.lower():
                        report_title = "NCRC Policy Brief"

                    records.append({
                        "source_name": self.name,
                        "report_year": year,
                        "report_title": f"{report_title} {year}",
                        "indicator": indicator,
                        "value": value,
                        "unit": unit,
                        "geographic_scope": province or "Pakistan",
                        "victim_gender": gender,
                        "victim_age_bracket": "0-18",
                        "pdf_url": pdf_url,
                        "extraction_method": "pdfplumber",
                        "extraction_confidence": 0.75,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    })

        return records

    def _extract_year(self, text: str) -> int | None:
        """Extract year from text.

        Args:
            text: Text to search for year.

        Returns:
            Year or None.
        """
        year_match = re.search(r"20[0-2]\d", text)
        if year_match:
            return int(year_match.group())
        return None

    def _parse_numeric(self, text: str) -> int | float | None:
        """Parse a numeric value from a string.

        Args:
            text: Raw cell text.

        Returns:
            Numeric value or None.
        """
        cleaned = text.strip().replace(",", "").replace("%", "").replace(" ", "")
        if not cleaned:
            return None
        try:
            if "." in cleaned:
                return float(cleaned)
            return int(cleaned)
        except ValueError:
            return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch NCRC pages, discover PDFs, download and extract data.

        Checks the main page and known sub-pages for PDF links.
        Gracefully continues if some pages are unreachable.

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

        # Check known sub-pages
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
        """Validate an NCRC statistical report record.

        Requires source_name and either indicator or report_title.
        """
        return bool(
            record.get("source_name")
            and (record.get("indicator") or record.get("report_title"))
        )
