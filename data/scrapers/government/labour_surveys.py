"""Pakistan Bureau of Statistics Labour Force Survey scraper.

Downloads and extracts child labor statistics from provincial Labour
Force Survey PDFs published by PBS. These surveys provide district-level
child labor prevalence data (e.g., 13.4% in Punjab) disaggregated by
province, gender, and urban/rural classification.

Source: https://www.pbs.gov.pk/content/labour-force-survey
Schedule: Annually (0 6 1 6 *)
Priority: P2 — National statistical authority data
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import logging
import re

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

# Provinces covered by labour force surveys
_PROVINCES: list[str] = [
    "Punjab",
    "Sindh",
    "Khyber Pakhtunkhwa",
    "Balochistan",
    "Islamabad Capital Territory",
]

# Keywords that identify child-labor-relevant tables in LFS PDFs
_CHILD_LABOR_KEYWORDS: list[str] = [
    "child lab",
    "child work",
    "economically active children",
    "working children",
    "5-14",
    "5-17",
    "10-14",
    "age group",
    "activity status",
    "employed children",
]


class LabourSurveysScraper(BasePDFReportScraper):
    """Scraper for PBS Labour Force Survey child labor statistics.

    Discovers LFS PDF links on the PBS page, downloads them,
    and extracts child labor prevalence tables. Produces
    statistical_reports records with province-level granularity.
    """

    name: str = "labour_surveys"
    source_url: str = "https://www.pbs.gov.pk/content/labour-force-survey"
    catalog_url: str = "https://www.pbs.gov.pk/content/labour-force-survey"
    schedule: str = "0 6 1 6 *"
    priority: str = "P2"
    rate_limit_delay: float = 3.0
    request_timeout: float = 90.0
    pdf_link_pattern: str = r"labour.*force|lfs|survey.*\d{4}.*\.pdf"

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch catalog, discover LFS PDFs, download, and extract tables."""
        logger.info("[%s] Fetching PBS catalogue: %s", self.name, self.catalog_url)

        response = await self.fetch(self.catalog_url)
        pdf_urls = self.discover_pdf_urls(response.text)

        # Also find PDFs via broader link scanning
        pdf_urls = self._find_additional_pdfs(response.text, pdf_urls)

        if not pdf_urls:
            logger.warning("[%s] No LFS PDF URLs found", self.name)
            return []

        logger.info("[%s] Found %d PDF URLs", self.name, len(pdf_urls))

        all_records: list[dict[str, Any]] = []
        for pdf_url in pdf_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)
                tables = self.extract_tables(pdf_path)
                text = self.extract_text(pdf_path)
                records = self.parse_tables(tables, pdf_url)

                if not records and text:
                    records = self._extract_from_text(text, pdf_url)

                all_records.extend(records)
            except Exception as exc:
                logger.error(
                    "[%s] Failed to process %s: %s", self.name, pdf_url, exc
                )

        return all_records

    def _find_additional_pdfs(
        self, html: str, existing: list[str]
    ) -> list[str]:
        """Find additional PDF links that the base pattern may have missed."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        existing_set = set(existing)

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".pdf" not in href.lower():
                continue
            text = link.get_text(strip=True).lower()
            if any(kw in text or kw in href.lower() for kw in ["labour", "lfs", "survey"]):
                full_url = (
                    href if href.startswith("http")
                    else f"https://www.pbs.gov.pk{href}"
                )
                if full_url not in existing_set:
                    existing.append(full_url)
                    existing_set.add(full_url)

        return existing

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Parse LFS tables for child labor statistics."""
        records: list[dict[str, Any]] = []
        year = self._extract_year(pdf_url)

        for table in tables:
            if not table or len(table) < 2:
                continue

            header_text = " ".join(
                str(cell).lower() for cell in table[0]
            )

            # Only process tables relevant to child labor / age groups
            if not any(kw in header_text for kw in _CHILD_LABOR_KEYWORDS):
                sample = " ".join(
                    str(cell).lower()
                    for row in table[1:5]
                    for cell in row
                )
                if not any(kw in sample for kw in _CHILD_LABOR_KEYWORDS):
                    continue

            headers = [str(cell).strip() for cell in table[0]]

            for row in table[1:]:
                cells = [str(cell).strip() for cell in row]
                if not any(cells):
                    continue

                row_label = cells[0] if cells else ""
                province = self._detect_province(row_label)

                # Extract numeric values from subsequent columns
                for col_idx in range(1, min(len(cells), len(headers))):
                    value = self._parse_numeric(cells[col_idx])
                    if value is None:
                        continue

                    col_name = headers[col_idx] if col_idx < len(headers) else ""
                    gender = self._detect_gender(col_name)

                    records.append({
                        "source_name": self.name,
                        "report_year": year,
                        "report_title": f"Pakistan Labour Force Survey {year}",
                        "indicator": f"lfs_{row_label}_{col_name}".strip("_"),
                        "value": value,
                        "unit": self._infer_unit(value),
                        "geographic_scope": province or "Pakistan",
                        "pdf_url": pdf_url,
                        "extraction_method": "pdf_table_pdfplumber",
                        "extraction_confidence": 0.70,
                        "victim_gender": gender,
                        "victim_age_bracket": self._detect_age_bracket(
                            row_label + " " + col_name
                        ),
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    })

        return records

    def _extract_from_text(
        self, text: str, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Fallback: extract child labor statistics from raw text."""
        records: list[dict[str, Any]] = []
        year = self._extract_year(pdf_url)

        # Pattern: "X.X% children" or "X.X percent"
        pct_pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*%?\s*(?:children|child|working\s+children)",
            re.IGNORECASE,
        )

        for match in pct_pattern.finditer(text):
            start = max(0, match.start() - 120)
            context = text[start:match.end() + 60].strip()

            province = None
            for prov in _PROVINCES:
                if prov.lower() in context.lower():
                    province = prov
                    break

            records.append({
                "source_name": self.name,
                "report_year": year,
                "report_title": f"Pakistan Labour Force Survey {year}",
                "indicator": f"lfs_text_extract: {context[:100]}",
                "value": float(match.group(1)),
                "unit": "percent",
                "geographic_scope": province or "Pakistan",
                "pdf_url": pdf_url,
                "extraction_method": "pdf_text_regex",
                "extraction_confidence": 0.45,
                "victim_gender": None,
                "victim_age_bracket": None,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })

        return records

    @staticmethod
    def _detect_province(text: str) -> str | None:
        """Detect a Pakistan province name in a text string."""
        text_lower = text.lower()
        for prov in _PROVINCES:
            if prov.lower() in text_lower:
                return prov
        # Common abbreviations
        abbrevs = {"kp": "Khyber Pakhtunkhwa", "kpk": "Khyber Pakhtunkhwa",
                    "ict": "Islamabad Capital Territory"}
        for abbrev, full in abbrevs.items():
            if abbrev == text_lower.strip():
                return full
        return None

    @staticmethod
    def _detect_gender(text: str) -> str | None:
        """Detect gender from a column header or label."""
        text_lower = text.lower()
        if "female" in text_lower or "girl" in text_lower or "women" in text_lower:
            return "female"
        if "male" in text_lower or "boy" in text_lower or "men" in text_lower:
            if "female" not in text_lower:
                return "male"
        if "total" in text_lower or "both" in text_lower:
            return "total"
        return None

    @staticmethod
    def _detect_age_bracket(text: str) -> str | None:
        """Detect age bracket from text."""
        match = re.search(r"(\d{1,2})\s*[-–]\s*(\d{1,2})", text)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return None

    @staticmethod
    def _extract_year(url_or_text: str) -> str:
        """Extract a 4-digit year from a URL or text string."""
        # Try year ranges first (e.g., 2023-24)
        range_match = re.search(r"(20[0-2]\d)[-–](\d{2})", url_or_text)
        if range_match:
            return range_match.group(1)
        single_match = re.search(r"20[0-2]\d", url_or_text)
        return single_match.group() if single_match else str(datetime.now(timezone.utc).year)

    @staticmethod
    def _parse_numeric(value_str: str) -> float | None:
        """Parse a numeric string."""
        cleaned = value_str.replace(",", "").replace(" ", "").strip()
        if not cleaned or cleaned == "-":
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _infer_unit(value: float) -> str:
        """Infer whether a value is a percentage or a count."""
        if 0 < value <= 100:
            return "percent"
        return "count"

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Labour Force Survey record."""
        if not record.get("source_name"):
            return False
        if not record.get("indicator") and not record.get("report_title"):
            return False
        if record.get("value") is None:
            return False
        return True
