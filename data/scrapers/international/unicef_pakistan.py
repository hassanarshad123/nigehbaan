"""UNICEF Pakistan child protection data scraper.

Scrapes UNICEF Pakistan's child protection page for PDF reports and
HTML-embedded statistics on birth registration, child labor, child
marriage, and other child protection indicators.

URL: https://www.unicef.org/pakistan/child-protection-0
Schedule: Quarterly (0 3 1 */3 *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

# Key child protection indicators tracked by UNICEF Pakistan
UNICEF_INDICATORS: list[str] = [
    "birth_registration",
    "child_labor",
    "child_marriage",
    "child_marriage_before_15",
    "child_marriage_before_18",
    "violent_discipline",
    "child_sexual_abuse",
    "child_trafficking",
    "female_genital_mutilation",
    "juvenile_justice",
    "children_in_detention",
    "orphans_vulnerable_children",
]

# UNICEF sub-pages that may contain additional data
UNICEF_DATA_PAGES: list[str] = [
    "https://www.unicef.org/pakistan/child-protection-0",
    "https://www.unicef.org/pakistan/reports",
    "https://www.unicef.org/pakistan/research-and-reports",
    "https://data.unicef.org/country/pak/",
]


class UNICEFPakistanScraper(BasePDFReportScraper):
    """Scraper for UNICEF Pakistan child protection data.

    Combines PDF report extraction with inline HTML statistics to
    capture birth registration rates, child labor prevalence, child
    marriage statistics, and other UNICEF-tracked indicators.
    """

    name: str = "unicef_pakistan"
    source_url: str = "https://www.unicef.org/pakistan/child-protection-0"
    catalog_url: str = "https://www.unicef.org/pakistan/child-protection-0"
    schedule: str = "0 3 1 */3 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    pdf_link_pattern: str = r"\.pdf"

    def _classify_indicator(self, text: str) -> str:
        """Map raw text to a standardized UNICEF indicator.

        Args:
            text: Raw text from table or page element.

        Returns:
            Standardized indicator name.
        """
        text_lower = text.lower()

        mapping: dict[str, list[str]] = {
            "birth_registration": ["birth registr", "registered at birth", "birth certificate"],
            "child_labor": ["child lab", "child work", "working children", "economic activity"],
            "child_marriage": ["child marriage", "early marriage", "married before"],
            "child_marriage_before_15": ["married before 15", "marriage before 15", "under 15"],
            "child_marriage_before_18": ["married before 18", "marriage before 18", "under 18"],
            "violent_discipline": ["violent discipline", "physical punishment", "corporal"],
            "child_sexual_abuse": ["sexual abuse", "sexual violence", "csa"],
            "child_trafficking": ["trafficking", "traffick"],
            "juvenile_justice": ["juvenile", "justice for children", "diversion"],
            "children_in_detention": ["detention", "incarcerated", "imprisoned"],
            "orphans_vulnerable_children": ["orphan", "ovc", "vulnerable children"],
        }

        for indicator, keywords in mapping.items():
            if any(kw in text_lower for kw in keywords):
                return indicator

        return text.strip()[:100]

    def _extract_year(self, text: str) -> int | None:
        """Extract a year from text content.

        Args:
            text: Text to search for year.

        Returns:
            Year or None.
        """
        year_match = re.search(r"20[0-2]\d", text)
        if year_match:
            return int(year_match.group())
        return None

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Parse PDF tables into statistical_reports records.

        Handles UNICEF data tables with indicators like birth
        registration rates, child labor percentages, and marriage stats.

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

                # Check for province-level breakdown
                province = None
                for i, header in enumerate(headers):
                    if "province" in header or "region" in header:
                        if i < len(row):
                            province = row[i].strip()
                            break

                # Extract numeric values — look for percentage or count columns
                for i, header in enumerate(headers):
                    if i == 0 or i >= len(row):
                        continue
                    cell = row[i].strip() if row[i] else ""
                    value = self._parse_value(cell)
                    if value is None:
                        continue

                    unit = "percent" if "%" in cell or "rate" in header else "count"

                    # Detect gender from header
                    gender = None
                    if any(kw in header for kw in ["male", "boy"]):
                        gender = "male"
                    elif any(kw in header for kw in ["female", "girl"]):
                        gender = "female"

                    records.append({
                        "source_name": self.name,
                        "report_year": year,
                        "report_title": f"UNICEF Pakistan Child Protection Report {year}",
                        "indicator": indicator,
                        "value": value,
                        "unit": unit,
                        "geographic_scope": province or "Pakistan",
                        "victim_gender": gender,
                        "victim_age_bracket": "0-18",
                        "pdf_url": pdf_url,
                        "extraction_method": "pdfplumber",
                        "extraction_confidence": 0.8,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    })

        return records

    def _parse_value(self, text: str) -> float | int | None:
        """Parse a string value, handling percentages and commas.

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

    def _extract_html_statistics(self, html: str) -> list[dict[str, Any]]:
        """Extract child protection statistics embedded in HTML.

        Parses both stat blocks (divs with numbers) and HTML tables
        on UNICEF Pakistan pages.

        Args:
            html: Raw HTML content.

        Returns:
            List of statistical_reports records.
        """
        soup = BeautifulSoup(html, "html.parser")
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Extract from stat/figure blocks
        for block in soup.find_all(["div", "section", "article"]):
            text = block.get_text(strip=True)
            if not text or len(text) > 1000:
                continue

            # Match patterns like "XX% of children" or "X.X million children"
            stat_patterns = [
                r"(\d[\d,.]*)\s*(%)\s*(?:of\s+)?(?:children|child|boys|girls)",
                r"(\d[\d,.]*)\s*(million|thousand)\s+(?:children|child)",
                r"(\d[\d,.]*)\s*(?:children|child|boys|girls)\s+(?:are|were|have)",
            ]

            for pattern in stat_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    raw_value = match.group(1).replace(",", "")
                    try:
                        value = float(raw_value) if "." in raw_value else int(raw_value)
                    except ValueError:
                        continue

                    unit = "percent" if "%" in match.group(0) else "count"
                    if len(match.groups()) > 1 and match.group(2).lower() == "million":
                        value = value * 1_000_000
                        unit = "count"

                    indicator = self._classify_indicator(text[:300])

                    records.append({
                        "source_name": self.name,
                        "report_year": self._extract_year(text) or now.year,
                        "report_title": "UNICEF Pakistan - Inline Statistics",
                        "indicator": indicator,
                        "value": value,
                        "unit": unit,
                        "geographic_scope": "Pakistan",
                        "victim_gender": None,
                        "victim_age_bracket": "0-18",
                        "pdf_url": self.source_url,
                        "extraction_method": "html_inline",
                        "extraction_confidence": 0.6,
                        "scraped_at": now.isoformat(),
                    })
                    break  # One match per block

        # Extract from HTML tables
        for table_el in soup.find_all("table"):
            header_row = table_el.find("tr")
            if not header_row:
                continue
            headers = [
                cell.get_text(strip=True).lower()
                for cell in header_row.find_all(["th", "td"])
            ]
            if not headers:
                continue

            for row in table_el.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not cells or len(cells) < 2:
                    continue

                indicator_text = cells[0]
                indicator = self._classify_indicator(indicator_text)

                for i, cell_text in enumerate(cells[1:], start=1):
                    value = self._parse_value(cell_text)
                    if value is None:
                        continue

                    records.append({
                        "source_name": self.name,
                        "report_year": self._extract_year(cell_text) or now.year,
                        "report_title": "UNICEF Pakistan - HTML Table Data",
                        "indicator": indicator,
                        "value": value,
                        "unit": "percent" if "%" in cell_text else "count",
                        "geographic_scope": "Pakistan",
                        "victim_gender": None,
                        "victim_age_bracket": "0-18",
                        "pdf_url": self.source_url,
                        "extraction_method": "html_table",
                        "extraction_confidence": 0.7,
                        "scraped_at": now.isoformat(),
                    })

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch UNICEF Pakistan pages, discover PDFs, and extract data.

        Combines PDF extraction with HTML-embedded statistics from
        multiple UNICEF Pakistan pages.

        Returns:
            List of statistical_reports records.
        """
        all_records: list[dict[str, Any]] = []
        all_pdf_urls: list[str] = []

        # Crawl all known UNICEF data pages
        for page_url in UNICEF_DATA_PAGES:
            try:
                response = await self.fetch(page_url)
                html = response.text

                # Extract HTML-embedded stats
                html_records = self._extract_html_statistics(html)
                all_records.extend(html_records)

                # Discover PDF links
                pdf_urls = self.discover_pdf_urls(html)
                all_pdf_urls.extend(pdf_urls)

                logger.info(
                    "[%s] Page %s: %d inline stats, %d PDF links",
                    self.name, page_url, len(html_records), len(pdf_urls),
                )
            except Exception as exc:
                logger.warning("[%s] Failed to fetch %s: %s", self.name, page_url, exc)

        # Deduplicate PDF URLs
        seen: set[str] = set()
        unique_pdf_urls: list[str] = []
        for url in all_pdf_urls:
            if url not in seen:
                seen.add(url)
                unique_pdf_urls.append(url)

        # Process PDFs
        for pdf_url in unique_pdf_urls:
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
        """Validate a UNICEF Pakistan statistical report record.

        Requires source_name and either indicator or report_title.
        """
        return bool(
            record.get("source_name")
            and (record.get("indicator") or record.get("report_title"))
        )
