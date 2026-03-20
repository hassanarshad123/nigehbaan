"""Sahil "Cruel Numbers" PDF report parser.

Parses all 16 Sahil annual "Cruel Numbers" reports (2010-2024)
which track child abuse cases across Pakistan.

Priority: P1
"""

from pathlib import Path
from typing import Any
import re

import logging

logger = logging.getLogger(__name__)

CRIME_CATEGORIES: list[str] = [
    "abduction", "kidnapping", "missing_children", "child_sexual_abuse",
    "sodomy", "gang_sodomy", "rape", "gang_rape", "attempt_sexual_abuse",
    "child_pornography", "child_marriage", "child_labour",
    "child_domestic_labour", "child_trafficking", "physical_abuse",
    "murder", "attempt_murder", "acid_attack", "honor_killing",
    "medical_negligence", "abandonment",
]

CATEGORY_ALIASES: dict[str, str] = {
    "abduction/kidnapping": "abduction",
    "sexual abuse": "child_sexual_abuse",
    "buggery/sodomy": "sodomy",
    "gang buggery": "gang_sodomy",
    "gang sexual abuse": "gang_rape",
    "attempt of sexual abuse": "attempt_sexual_abuse",
    "pornography": "child_pornography",
    "early/child marriage": "child_marriage",
    "child marriages": "child_marriage",
    "child labour": "child_labour",
    "domestic child labour": "child_domestic_labour",
    "trafficking": "child_trafficking",
    "physical violence": "physical_abuse",
    "emotional abuse": "physical_abuse",
    "killing/murder": "murder",
    "attempted murder": "attempt_murder",
    "acid throwing": "acid_attack",
    "honour killing": "honor_killing",
    "karo kari": "honor_killing",
    "missing children": "missing_children",
    "abandonment/exposure": "abandonment",
}

PROVINCE_ALIASES: dict[str, str] = {
    "kp": "Khyber Pakhtunkhwa",
    "kpk": "Khyber Pakhtunkhwa",
    "nwfp": "Khyber Pakhtunkhwa",
    "khyber pakhtunkhwa": "Khyber Pakhtunkhwa",
    "punjab": "Punjab",
    "sindh": "Sindh",
    "balochistan": "Balochistan",
    "baluchistan": "Balochistan",
    "ict": "Islamabad Capital Territory",
    "islamabad": "Islamabad Capital Territory",
    "ajk": "Azad Jammu & Kashmir",
    "azad kashmir": "Azad Jammu & Kashmir",
    "gb": "Gilgit-Baltistan",
    "gilgit baltistan": "Gilgit-Baltistan",
    "fata": "FATA",
}

# Known published totals for validation
KNOWN_TOTALS: dict[int, int] = {
    2024: 4266,
    2023: 4213,
    2022: 4253,
    2021: 3852,
    2020: 2960,
    2019: 3832,
    2018: 3832,
}


class SahilParser:
    """Parser for Sahil 'Cruel Numbers' annual PDF reports."""

    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir

    def parse_report(
        self, pdf_path: Path, year: int
    ) -> list[dict[str, Any]]:
        """Parse a single Sahil annual report PDF."""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed")
            return []

        tables = self.extract_tables(pdf_path)
        if not tables:
            logger.warning("No tables found in %s", pdf_path)
            return []

        records: list[dict[str, Any]] = []
        for table in tables:
            parsed = self._parse_table_to_records(table, year)
            records.extend(parsed)

        records = self.normalize_categories(records)
        records = self.normalize_provinces(records)
        return records

    def _parse_table_to_records(
        self, table: list[list[str]], year: int
    ) -> list[dict[str, Any]]:
        """Convert a raw table (list of rows) into record dicts."""
        if not table or len(table) < 2:
            return []

        records: list[dict[str, Any]] = []
        headers = [h.strip().lower() if h else "" for h in table[0]]

        # Detect if this is a province breakdown table or summary table
        has_province = any("province" in h or "region" in h for h in headers)
        has_category = any("category" in h or "type" in h or "offence" in h or "crime" in h for h in headers)

        for row in table[1:]:
            if not row or all(not cell for cell in row):
                continue

            record: dict[str, Any] = {"year": year}
            for i, cell in enumerate(row):
                if i < len(headers):
                    key = headers[i]
                    value = cell.strip() if cell else ""

                    # Try to parse as integer
                    num_match = re.match(r"^[\d,]+$", value.replace(" ", ""))
                    if num_match:
                        record[key] = int(value.replace(",", "").replace(" ", ""))
                    else:
                        record[key] = value

            # Map to standardized fields
            normalized: dict[str, Any] = {"year": year}
            for key, value in record.items():
                if any(kw in key for kw in ["category", "type", "offence", "crime"]):
                    normalized["crime_category"] = str(value)
                elif any(kw in key for kw in ["province", "region"]):
                    normalized["province"] = str(value)
                elif any(kw in key for kw in ["total", "count", "cases", "number"]):
                    normalized["case_count"] = value if isinstance(value, int) else 0
                elif any(kw in key for kw in ["male", "boy"]):
                    normalized["victim_gender"] = "male"
                    if isinstance(value, int):
                        normalized["case_count"] = value
                elif any(kw in key for kw in ["female", "girl"]):
                    normalized["victim_gender"] = "female"
                    if isinstance(value, int):
                        normalized["case_count"] = value
                else:
                    normalized[key] = value

            if normalized.get("crime_category") or normalized.get("case_count"):
                records.append(normalized)

        return records

    def extract_tables(self, pdf_path: Path) -> list[list[list[str]]]:
        """Extract all tables from a PDF using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed")
            return []

        tables: list[list[list[str]]] = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            cleaned = [
                                [cell or "" for cell in row]
                                for row in table
                                if row
                            ]
                            if cleaned and len(cleaned) > 1:
                                tables.append(cleaned)
        except Exception as exc:
            logger.error("Error extracting tables from %s: %s", pdf_path, exc)
            # Try tabula fallback
            fallback = self.extract_tables_tabula(pdf_path)
            if fallback:
                tables.extend(fallback)

        return tables

    def extract_tables_tabula(
        self, pdf_path: Path, pages: str = "all"
    ) -> list[list[list[str]]]:
        """Fallback table extraction using tabula-py."""
        try:
            import tabula
        except ImportError:
            logger.warning("tabula-py not installed, skipping fallback")
            return []

        tables: list[list[list[str]]] = []
        try:
            dfs = tabula.read_pdf(str(pdf_path), pages=pages, lattice=True)
            for df in dfs:
                header = [str(c) for c in df.columns.tolist()]
                rows = [[str(cell) if cell else "" for cell in row] for row in df.values.tolist()]
                tables.append([header] + rows)
        except Exception:
            try:
                dfs = tabula.read_pdf(str(pdf_path), pages=pages, stream=True)
                for df in dfs:
                    header = [str(c) for c in df.columns.tolist()]
                    rows = [[str(cell) if cell else "" for cell in row] for row in df.values.tolist()]
                    tables.append([header] + rows)
            except Exception as exc:
                logger.error("Tabula fallback also failed: %s", exc)

        return tables

    def normalize_categories(
        self, raw_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Normalize crime category names across report years."""
        for record in raw_data:
            cat = record.get("crime_category", "")
            if isinstance(cat, str):
                cat_lower = cat.strip().lower()
                if cat_lower in CATEGORY_ALIASES:
                    record["crime_category"] = CATEGORY_ALIASES[cat_lower]
                elif cat_lower.replace(" ", "_") in CRIME_CATEGORIES:
                    record["crime_category"] = cat_lower.replace(" ", "_")
        return raw_data

    def normalize_provinces(
        self, raw_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Normalize province names across records."""
        for record in raw_data:
            prov = record.get("province", "")
            if isinstance(prov, str):
                prov_lower = prov.strip().lower()
                if prov_lower in PROVINCE_ALIASES:
                    record["province"] = PROVINCE_ALIASES[prov_lower]
        return raw_data

    def parse_all_reports(self) -> list[dict[str, Any]]:
        """Parse all Sahil reports in the reports directory."""
        if not self.reports_dir.exists():
            logger.warning("Reports dir does not exist: %s", self.reports_dir)
            return []

        all_records: list[dict[str, Any]] = []
        for pdf_path in sorted(self.reports_dir.glob("*.pdf")):
            # Extract year from filename
            year_match = re.search(r"20[0-2]\d", pdf_path.stem)
            if not year_match:
                logger.warning("Could not determine year for %s", pdf_path)
                continue

            year = int(year_match.group())
            logger.info("Parsing Sahil report for year %d: %s", year, pdf_path.name)
            records = self.parse_report(pdf_path, year)
            all_records.extend(records)

        return all_records

    def validate_totals(
        self, records: list[dict[str, Any]], year: int
    ) -> bool:
        """Validate extracted data against known annual totals."""
        year_records = [r for r in records if r.get("year") == year]
        total = sum(r.get("case_count", 0) for r in year_records if isinstance(r.get("case_count"), int))

        known = KNOWN_TOTALS.get(year)
        if known is None:
            return True  # No known total to validate against

        tolerance = 0.05
        is_valid = abs(total - known) / known <= tolerance
        if not is_valid:
            logger.warning(
                "Year %d: extracted total %d vs known %d (diff %.1f%%)",
                year, total, known, abs(total - known) / known * 100,
            )
        return is_valid
