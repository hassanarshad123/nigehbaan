"""SSDO report parser.

Parses SSDO (Society for the Protection of the Rights of the Child)
PDF reports for child protection statistics with conviction rates.

Priority: P1
"""

from pathlib import Path
from typing import Any
import re

import logging

logger = logging.getLogger(__name__)


class SSDOParser:
    """Parser for SSDO child protection reports."""

    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir

    def parse_report(self, pdf_path: Path) -> dict[str, Any]:
        """Parse a single SSDO report PDF."""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed")
            return {}

        result: dict[str, Any] = {
            "file": str(pdf_path),
            "total_cases_by_category": {},
            "provincial_breakdown": {},
            "conviction_rates": {},
        }

        # Extract year from filename
        year_match = re.search(r"20[0-2]\d", pdf_path.stem)
        if year_match:
            result["year"] = int(year_match.group())

        case_counts = self.extract_case_counts(pdf_path)
        provincial = self.extract_provincial_breakdown(pdf_path)
        convictions = self.extract_conviction_rates(pdf_path)

        result["total_cases_by_category"] = case_counts
        result["provincial_breakdown"] = provincial
        result["conviction_rates"] = convictions

        return result

    def extract_case_counts(self, pdf_path: Path) -> dict[str, int]:
        """Extract total case counts by crime category."""
        try:
            import pdfplumber
        except ImportError:
            return {}

        counts: dict[str, int] = {}
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in (tables or []):
                        if not table or len(table) < 2:
                            continue
                        for row in table[1:]:
                            if not row or len(row) < 2:
                                continue
                            category = (row[0] or "").strip()
                            if not category:
                                continue
                            # Find the total/count column (usually last or second column)
                            for cell in reversed(row[1:]):
                                if cell and re.match(r"^[\d,]+$", str(cell).strip().replace(",", "")):
                                    counts[category] = int(str(cell).strip().replace(",", ""))
                                    break
        except Exception as exc:
            logger.error("Error extracting case counts from %s: %s", pdf_path, exc)

        return counts

    def extract_provincial_breakdown(
        self, pdf_path: Path
    ) -> dict[str, dict[str, int]]:
        """Extract case counts broken down by province."""
        try:
            import pdfplumber
        except ImportError:
            return {}

        provincial: dict[str, dict[str, int]] = {}
        provinces = {"punjab", "sindh", "kp", "khyber pakhtunkhwa", "balochistan", "islamabad", "ajk", "gb"}

        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in (tables or []):
                        if not table or len(table) < 2:
                            continue
                        headers = [
                            (h or "").strip().lower() for h in table[0]
                        ]
                        # Check if this looks like a provincial table
                        has_province_cols = any(
                            any(p in h for p in provinces)
                            for h in headers
                        )
                        if not has_province_cols:
                            continue

                        for row in table[1:]:
                            if not row or not row[0]:
                                continue
                            category = row[0].strip()
                            for i, header in enumerate(headers):
                                if i < len(row) and row[i]:
                                    for prov in provinces:
                                        if prov in header:
                                            val = str(row[i]).strip().replace(",", "")
                                            if val.isdigit():
                                                if prov not in provincial:
                                                    provincial[prov] = {}
                                                provincial[prov][category] = int(val)
        except Exception as exc:
            logger.error("Error extracting provincial data from %s: %s", pdf_path, exc)

        return provincial

    def extract_conviction_rates(
        self, pdf_path: Path
    ) -> dict[str, float]:
        """Extract conviction rates by crime category."""
        try:
            import pdfplumber
        except ImportError:
            return {}

        rates: dict[str, float] = {}
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"

                    tables = page.extract_tables()
                    for table in (tables or []):
                        if not table or len(table) < 2:
                            continue
                        headers = [(h or "").strip().lower() for h in table[0]]
                        has_conviction = any("convict" in h for h in headers)
                        has_cases = any("case" in h or "filed" in h or "registered" in h for h in headers)

                        if has_conviction and has_cases:
                            case_col = None
                            conv_col = None
                            for i, h in enumerate(headers):
                                if "case" in h or "filed" in h or "registered" in h:
                                    case_col = i
                                if "convict" in h:
                                    conv_col = i

                            if case_col is not None and conv_col is not None:
                                for row in table[1:]:
                                    if not row or not row[0]:
                                        continue
                                    category = row[0].strip()
                                    cases_str = str(row[case_col] or "").strip().replace(",", "")
                                    conv_str = str(row[conv_col] or "").strip().replace(",", "")
                                    if cases_str.isdigit() and conv_str.isdigit():
                                        cases = int(cases_str)
                                        convictions = int(conv_str)
                                        if cases > 0:
                                            rates[category] = convictions / cases

                # Also look for conviction rates in text
                rate_pattern = re.compile(
                    r"conviction\s+rate\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*%",
                    re.IGNORECASE,
                )
                for match in rate_pattern.finditer(full_text):
                    rate_val = float(match.group(1)) / 100.0
                    # Get context for category
                    start = max(0, match.start() - 100)
                    context = full_text[start:match.start()]
                    rates[f"context_{match.start()}"] = rate_val

        except Exception as exc:
            logger.error("Error extracting conviction rates from %s: %s", pdf_path, exc)

        return rates

    def parse_all_reports(self) -> list[dict[str, Any]]:
        """Parse all SSDO reports in the reports directory."""
        if not self.reports_dir.exists():
            logger.warning("Reports dir does not exist: %s", self.reports_dir)
            return []

        results: list[dict[str, Any]] = []
        for pdf_path in sorted(self.reports_dir.glob("*.pdf")):
            logger.info("Parsing SSDO report: %s", pdf_path.name)
            result = self.parse_report(pdf_path)
            if result:
                results.append(result)

        return results
