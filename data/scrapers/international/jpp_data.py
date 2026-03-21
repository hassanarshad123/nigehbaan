"""Justice Project Pakistan (JPP) data portal scraper.

Scrapes HTML tables from the JPP data portal for juvenile justice
statistics, including prison population, children in detention,
and related criminal justice indicators for Pakistan.

Source: https://data.jpp.org.pk/
Schedule: Quarterly (0 7 1 */3 *)
Priority: P1 — Key Pakistani juvenile justice data source
"""

from datetime import datetime, timezone
from typing import Any

import logging
import re

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

JPP_BASE_URL: str = "https://data.jpp.org.pk"

# Pages likely to contain juvenile justice / child detention data
TARGET_PATHS: list[str] = [
    "/",
    "/juvenile-justice",
    "/prison-population",
    "/children-in-detention",
    "/death-row",
    "/data",
]

# Keywords to identify relevant data tables
JUVENILE_KEYWORDS: list[str] = [
    "juvenile", "child", "minor", "under 18", "under-18",
    "young offender", "youth", "detention", "borstal",
    "reformatory", "prison population", "pretrial",
    "pre-trial", "remand",
]


class JPPDataScraper(BaseScraper):
    """Scraper for Justice Project Pakistan data portal.

    Fetches HTML pages from the JPP data portal, extracts data tables
    related to juvenile justice and children in detention, and parses
    them into statistical_reports formatted records.
    """

    name: str = "jpp_data"
    source_url: str = "https://data.jpp.org.pk/"
    schedule: str = "0 7 1 */3 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0
    request_timeout: float = 30.0

    async def _fetch_page(self, path: str) -> str | None:
        """Fetch a single page from the JPP data portal.

        Args:
            path: URL path relative to JPP_BASE_URL.

        Returns:
            HTML content string, or None on failure.
        """
        url = f"{JPP_BASE_URL}{path}"
        try:
            response = await self.fetch(url)
            return response.text
        except Exception as exc:
            logger.warning("[%s] Failed to fetch %s: %s", self.name, url, exc)
            return None

    @staticmethod
    def _extract_tables(html: str) -> list[list[list[str]]]:
        """Extract all HTML tables from page content using BeautifulSoup.

        Args:
            html: Raw HTML content string.

        Returns:
            List of tables, each table is a list of rows, each row a
            list of cell text values.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup (bs4) is required for JPP scraper")
            return []

        soup = BeautifulSoup(html, "html.parser")
        tables: list[list[list[str]]] = []

        for table_el in soup.find_all("table"):
            rows: list[list[str]] = []
            for tr in table_el.find_all("tr"):
                cells = [
                    td.get_text(strip=True)
                    for td in tr.find_all(["th", "td"])
                ]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)

        return tables

    @staticmethod
    def _is_relevant_table(
        table: list[list[str]],
    ) -> bool:
        """Check if a table contains juvenile justice related data.

        Args:
            table: Parsed table as list of row lists.

        Returns:
            True if any cell matches juvenile justice keywords.
        """
        table_text = " ".join(
            cell for row in table for cell in row
        ).lower()
        return any(kw in table_text for kw in JUVENILE_KEYWORDS)

    def _parse_table_to_records(
        self,
        table: list[list[str]],
        page_url: str,
    ) -> list[dict[str, Any]]:
        """Parse a single HTML table into statistical_reports records.

        Assumes the first row is headers. For each subsequent row,
        attempts to extract year, indicator name, and numeric value.

        Args:
            table: Parsed table as list of row lists.
            page_url: URL the table was found on (for provenance).

        Returns:
            List of statistical_reports formatted records.
        """
        if len(table) < 2:
            return []

        headers = [h.strip().lower() for h in table[0]]
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        # Try to identify year and value columns
        year_col = self._find_column_index(headers, ["year", "date", "period"])
        value_col = self._find_column_index(
            headers, ["value", "number", "count", "total", "population", "rate", "%"]
        )
        indicator_col = self._find_column_index(
            headers, ["indicator", "category", "type", "offence", "offense", "crime"]
        )

        for row in table[1:]:
            if len(row) <= max(
                c for c in [year_col, value_col, indicator_col] if c is not None
            ) if any(c is not None for c in [year_col, value_col, indicator_col]) else len(row) < 2:
                continue

            record = self._build_record_from_row(
                row, headers, year_col, value_col, indicator_col, page_url, now
            )
            if record is not None:
                records.append(record)

        return records

    def _build_record_from_row(
        self,
        row: list[str],
        headers: list[str],
        year_col: int | None,
        value_col: int | None,
        indicator_col: int | None,
        page_url: str,
        scraped_at: str,
    ) -> dict[str, Any] | None:
        """Build a single record from a table row.

        Args:
            row: List of cell values for this row.
            headers: Column header strings.
            year_col: Index of year column, or None.
            value_col: Index of value column, or None.
            indicator_col: Index of indicator column, or None.
            page_url: Source page URL.
            scraped_at: Timestamp string.

        Returns:
            Formatted record dict, or None if extraction fails.
        """
        # Extract year
        year = None
        if year_col is not None and year_col < len(row):
            year = self._extract_year(row[year_col])

        # Extract numeric value — try explicit column first, then scan row
        value = None
        if value_col is not None and value_col < len(row):
            value = self._parse_number(row[value_col])

        if value is None:
            # Scan remaining cells for a number
            for idx, cell in enumerate(row):
                if idx in (year_col, indicator_col):
                    continue
                parsed = self._parse_number(cell)
                if parsed is not None:
                    value = parsed
                    break

        if value is None:
            return None

        # Extract indicator name
        indicator = "unknown"
        if indicator_col is not None and indicator_col < len(row):
            indicator = row[indicator_col].strip()
        elif len(row) > 0:
            # Use first non-numeric cell as indicator
            for cell in row:
                if not self._parse_number(cell) and cell.strip():
                    indicator = cell.strip()
                    break

        # Determine unit from value context
        unit = "count"
        if any(h in headers for h in ["%", "rate", "percentage"]):
            unit = "percent"

        return {
            "source_name": "jpp_data",
            "report_year": str(year) if year else None,
            "report_title": f"JPP Data — {indicator} — Pakistan {year or 'N/A'}",
            "indicator": self._slugify(indicator),
            "indicator_label": indicator,
            "value": value,
            "unit": unit,
            "geographic_scope": "Pakistan",
            "pdf_url": None,
            "extraction_method": "html_table",
            "extraction_confidence": 0.75,
            "source_page": page_url,
            "scraped_at": scraped_at,
        }

    @staticmethod
    def _find_column_index(
        headers: list[str], candidates: list[str]
    ) -> int | None:
        """Find the index of a column matching any candidate name.

        Args:
            headers: Lowercased header strings.
            candidates: Possible header name substrings.

        Returns:
            Column index, or None if not found.
        """
        for idx, header in enumerate(headers):
            if any(c in header for c in candidates):
                return idx
        return None

    @staticmethod
    def _extract_year(text: str) -> int | None:
        """Extract a 4-digit year from text.

        Args:
            text: Cell text that may contain a year.

        Returns:
            Year as integer, or None.
        """
        match = re.search(r"\b(19|20)\d{2}\b", text)
        if match:
            return int(match.group(0))
        return None

    @staticmethod
    def _parse_number(text: str) -> float | None:
        """Parse a numeric value from cell text, handling commas.

        Args:
            text: Cell text that may contain a number.

        Returns:
            Parsed float, or None if not a number.
        """
        cleaned = text.strip().replace(",", "").replace("%", "").strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert indicator text to a slug identifier.

        Args:
            text: Human-readable indicator name.

        Returns:
            Lowercased, underscore-separated slug.
        """
        slug = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
        slug = re.sub(r"\s+", "_", slug.strip())
        return slug[:80] if slug else "unknown"

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the JPP data portal scraping pipeline.

        Iterates over target pages, extracts relevant HTML tables,
        and parses them into statistical_reports records.

        Returns:
            List of statistical_reports records for juvenile justice
            and child detention indicators.
        """
        all_records: list[dict[str, Any]] = []

        for path in TARGET_PATHS:
            html = await self._fetch_page(path)
            if html is None:
                continue

            page_url = f"{JPP_BASE_URL}{path}"
            tables = self._extract_tables(html)
            logger.info(
                "[%s] Found %d tables on %s",
                self.name, len(tables), page_url,
            )

            for table in tables:
                if not self._is_relevant_table(table):
                    continue

                records = self._parse_table_to_records(table, page_url)
                all_records.extend(records)
                logger.info(
                    "[%s] Extracted %d records from table on %s",
                    self.name, len(records), page_url,
                )

        logger.info(
            "[%s] Total: %d records from %d pages",
            self.name, len(all_records), len(TARGET_PATHS),
        )
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a JPP data statistical_reports record.

        Requires source_name, indicator, and a numeric value.
        Report year is optional since some tables may lack dates.
        """
        if not record.get("source_name"):
            return False
        if not record.get("indicator"):
            return False
        if record.get("value") is None:
            return False
        return True
