"""ZARRA report parser.

Parses Ministry of Human Rights ZARRA (Zero Abuse, Rape, and
Trafficking Assessment) PDF analysis reports.

Priority: P1
"""

from pathlib import Path
from typing import Any
import json
import re

import logging

logger = logging.getLogger(__name__)

DEFAULT_GAZETTEER_PATH = Path("data/config/gazetteer/pakistan_districts.json")


class ZARRAParser:
    """Parser for MoHR ZARRA assessment reports."""

    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir

    def parse_report(
        self, pdf_path: Path, year: int | None = None
    ) -> dict[str, Any]:
        """Parse a single ZARRA report PDF."""
        try:
            import pdfplumber  # noqa: F401
        except ImportError:
            logger.error("pdfplumber not installed")
            return {}

        result: dict[str, Any] = {"file": str(pdf_path)}

        if year is None:
            year_match = re.search(r"20[0-2]\d", pdf_path.stem)
            if year_match:
                year = int(year_match.group())
        result["year"] = year

        district_cases = self.extract_district_cases(pdf_path)
        case_status = self.extract_case_status(pdf_path)
        provincial = self.extract_provincial_distribution(pdf_path)

        result["district_cases"] = district_cases
        result["case_status_breakdown"] = case_status
        result["provincial_summary"] = provincial

        return result

    def extract_district_cases(
        self, pdf_path: Path
    ) -> list[dict[str, Any]]:
        """Extract district-level case count data."""
        try:
            import pdfplumber
        except ImportError:
            return []

        records: list[dict[str, Any]] = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in (tables or []):
                        if not table or len(table) < 2:
                            continue

                        headers = [(h or "").strip().lower() for h in table[0]]
                        has_district = any("district" in h for h in headers)
                        if not has_district:
                            continue

                        dist_col = next(
                            (i for i, h in enumerate(headers) if "district" in h), 0
                        )

                        for row in table[1:]:
                            if not row or not row[dist_col]:
                                continue
                            record: dict[str, Any] = {
                                "district": str(row[dist_col]).strip(),
                            }

                            for i, header in enumerate(headers):
                                if i == dist_col or i >= len(row):
                                    continue
                                val = str(row[i] or "").strip().replace(",", "")
                                if val.isdigit():
                                    record[header] = int(val)
                                elif val:
                                    record[header] = val

                            if record.get("district"):
                                records.append(record)

        except Exception as exc:
            logger.error("Error extracting district cases from %s: %s", pdf_path, exc)

        return records

    def extract_case_status(
        self, pdf_path: Path
    ) -> dict[str, int]:
        """Extract case status breakdown."""
        try:
            import pdfplumber
        except ImportError:
            return {}

        status: dict[str, int] = {}
        status_keywords = {"active", "recovered", "closed", "pending", "resolved", "in progress"}

        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"

                    tables = page.extract_tables()
                    for table in (tables or []):
                        for row in (table or []):
                            if not row or len(row) < 2:
                                continue
                            label = str(row[0] or "").strip().lower()
                            for kw in status_keywords:
                                if kw in label:
                                    for cell in row[1:]:
                                        val = str(cell or "").strip().replace(",", "")
                                        if val.isdigit():
                                            status[kw] = int(val)
                                            break

                # Text-based extraction
                for kw in status_keywords:
                    if kw not in status:
                        pattern = re.compile(
                            rf"{kw}\s*[:\-–]\s*(\d+(?:,\d+)*)",
                            re.IGNORECASE,
                        )
                        match = pattern.search(full_text)
                        if match:
                            status[kw] = int(match.group(1).replace(",", ""))

        except Exception as exc:
            logger.error("Error extracting case status from %s: %s", pdf_path, exc)

        return status

    def extract_provincial_distribution(
        self, pdf_path: Path
    ) -> dict[str, int]:
        """Extract provincial distribution of cases."""
        try:
            import pdfplumber
        except ImportError:
            return {}

        provincial: dict[str, int] = {}
        provinces = ["punjab", "sindh", "khyber pakhtunkhwa", "kp", "balochistan", "islamabad", "ict"]

        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in (tables or []):
                        for row in (table or []):
                            if not row or len(row) < 2:
                                continue
                            label = str(row[0] or "").strip().lower()
                            for prov in provinces:
                                if prov in label:
                                    for cell in row[1:]:
                                        val = str(cell or "").strip().replace(",", "")
                                        if val.isdigit():
                                            provincial[prov.title()] = int(val)
                                            break
        except Exception as exc:
            logger.error("Error extracting provincial data from %s: %s", pdf_path, exc)

        return provincial

    def geocode_districts(
        self,
        records: list[dict[str, Any]],
        gazetteer_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Add P-codes to district records using the gazetteer."""
        gaz_path = gazetteer_path or DEFAULT_GAZETTEER_PATH
        if not gaz_path.exists():
            logger.warning("Gazetteer not found: %s", gaz_path)
            return records

        try:
            gaz_data = json.loads(gaz_path.read_text(encoding="utf-8"))
            districts = gaz_data.get("districts", [])

            # Build lookup: lowercase variants → pcode
            lookup: dict[str, str] = {}
            for d in districts:
                pcode = d.get("pcode", "")
                for variant in d.get("variants", []):
                    lookup[variant.lower()] = pcode
                lookup[d.get("name_en", "").lower()] = pcode

            for record in records:
                district_name = record.get("district", "")
                if district_name:
                    pcode = lookup.get(district_name.lower())
                    if pcode:
                        record["district_pcode"] = pcode
                    else:
                        # Fuzzy fallback: check if any key contains the district name
                        for key, val in lookup.items():
                            if district_name.lower() in key or key in district_name.lower():
                                record["district_pcode"] = val
                                break
                        if "district_pcode" not in record:
                            record["district_pcode"] = None
                            logger.debug("Unmatched district: %s", district_name)

        except Exception as exc:
            logger.error("Error geocoding districts: %s", exc)

        return records

    def parse_all_reports(self) -> list[dict[str, Any]]:
        """Parse all ZARRA reports in the reports directory."""
        if not self.reports_dir.exists():
            logger.warning("Reports dir does not exist: %s", self.reports_dir)
            return []

        results: list[dict[str, Any]] = []
        for pdf_path in sorted(self.reports_dir.glob("*.pdf")):
            logger.info("Parsing ZARRA report: %s", pdf_path.name)
            result = self.parse_report(pdf_path)
            if result.get("district_cases"):
                results.append(result)

        return results
