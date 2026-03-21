"""Girls Not Brides Pakistan child marriage atlas scraper.

Scrapes the Girls Not Brides child marriage atlas page for Pakistan,
extracting child marriage prevalence statistics, key indicators,
infographic data, and legal framework information.

URL: https://www.girlsnotbrides.org/learning-resources/child-marriage-atlas/regions-and-countries/pakistan/
Schedule: Annually (0 0 1 2 *)
Priority: P2
"""

from datetime import datetime, timezone
from typing import Any
import re

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Wayback Machine base URL for fallback
WAYBACK_BASE = "https://web.archive.org/web/2024"

# Known indicators tracked on the Girls Not Brides atlas
GNB_INDICATORS: list[str] = [
    "married_by_15",
    "married_by_18",
    "child_marriage_prevalence",
    "girls_affected",
    "legal_minimum_age_marriage",
    "gender_inequality_index",
    "adolescent_birth_rate",
    "female_secondary_education",
    "population_under_18",
]


class GirlsNotBridesScraper(BaseScraper):
    """Scraper for Girls Not Brides child marriage atlas — Pakistan.

    Parses the Pakistan country page for child marriage prevalence
    statistics, data tables, infographic stat blocks, and legal
    framework indicators. Falls back to Wayback Machine if the
    live site is unreachable.
    """

    name: str = "girls_not_brides"
    source_url: str = (
        "https://www.girlsnotbrides.org/learning-resources/"
        "child-marriage-atlas/regions-and-countries/pakistan/"
    )
    schedule: str = "0 0 1 2 *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0

    def _classify_indicator(self, text: str) -> str:
        """Map raw text to a standardized GNB indicator.

        Args:
            text: Raw text from a stat block, table cell, or heading.

        Returns:
            Standardized indicator name.
        """
        text_lower = text.lower()

        mapping: dict[str, list[str]] = {
            "married_by_15": [
                "married by 15", "before 15", "by age 15",
                "married before age 15", "under 15",
            ],
            "married_by_18": [
                "married by 18", "before 18", "by age 18",
                "married before age 18", "under 18",
            ],
            "child_marriage_prevalence": [
                "prevalence", "child marriage rate", "overall rate",
            ],
            "girls_affected": [
                "girls affected", "number of girls", "girls married",
            ],
            "legal_minimum_age_marriage": [
                "legal age", "minimum age", "legal minimum",
                "age of marriage", "marriageable age",
            ],
            "gender_inequality_index": [
                "gender inequality", "gii", "inequality index",
            ],
            "adolescent_birth_rate": [
                "adolescent birth", "birth rate", "fertility rate",
            ],
            "female_secondary_education": [
                "secondary education", "school", "education",
            ],
            "population_under_18": [
                "population under 18", "population aged", "youth population",
            ],
        }

        for indicator, keywords in mapping.items():
            if any(kw in text_lower for kw in keywords):
                return indicator

        return text.strip()[:100]

    def _parse_value(self, text: str) -> float | int | None:
        """Parse a numeric value from text, handling percentages and commas.

        Args:
            text: Raw text that may contain a number.

        Returns:
            Numeric value or None if unparseable.
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

    def _extract_year(self, text: str) -> int | None:
        """Extract a four-digit year from text.

        Args:
            text: Text to search for a year.

        Returns:
            Year as integer or None.
        """
        year_match = re.search(r"20[0-2]\d", text)
        if year_match:
            return int(year_match.group())
        return None

    def _extract_stat_blocks(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract statistics from infographic-style stat blocks.

        Girls Not Brides pages display key stats in prominent blocks
        with large numbers and descriptive labels.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Look for stat blocks — divs/sections with prominent numbers
        stat_patterns = [
            r"(\d[\d,.]*)\s*(%)\s*(?:of\s+)?(?:girls?|women|children)",
            r"(\d[\d,.]*)\s*(%)\s*.*?(?:married|marriage)",
            r"(\d[\d,.]*)\s*(million|thousand)\s+(?:girls?|women|children)",
            r"(\d[\d,.]*)\s*(?:girls?|women|children)\s+(?:are|were)",
        ]

        for block in soup.find_all(["div", "section", "article", "span", "p"]):
            text = block.get_text(separator=" ", strip=True)
            if not text or len(text) > 800:
                continue

            for pattern in stat_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if not match:
                    continue

                raw_value = match.group(1).replace(",", "")
                try:
                    value: float | int = (
                        float(raw_value) if "." in raw_value else int(raw_value)
                    )
                except ValueError:
                    continue

                unit = "percent"
                if len(match.groups()) > 1:
                    group2 = match.group(2).lower()
                    if group2 == "million":
                        value = value * 1_000_000
                        unit = "count"
                    elif group2 == "thousand":
                        value = value * 1_000
                        unit = "count"
                    elif group2 != "%":
                        unit = "count"

                indicator = self._classify_indicator(text[:300])

                records.append({
                    "source_name": self.name,
                    "report_year": self._extract_year(text) or now.year,
                    "report_title": "Girls Not Brides - Child Marriage Atlas Pakistan",
                    "indicator": indicator,
                    "value": value,
                    "unit": unit,
                    "geographic_scope": "Pakistan",
                    "extraction_method": "html_stat_block",
                    "extraction_confidence": 0.7,
                    "scraped_at": now.isoformat(),
                })
                break  # One match per block to avoid duplicates

        return records

    def _extract_tables(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract data from HTML tables on the page.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for table in soup.find_all("table"):
            header_row = table.find("tr")
            if not header_row:
                continue

            headers = [
                cell.get_text(strip=True).lower()
                for cell in header_row.find_all(["th", "td"])
            ]
            if not headers:
                continue

            for row in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not cells or len(cells) < 2:
                    continue

                indicator_text = cells[0]
                indicator = self._classify_indicator(indicator_text)

                for i, cell_text in enumerate(cells[1:], start=1):
                    value = self._parse_value(cell_text)
                    if value is None:
                        continue

                    unit = "percent" if "%" in cell_text else "count"

                    records.append({
                        "source_name": self.name,
                        "report_year": self._extract_year(cell_text) or now.year,
                        "report_title": "Girls Not Brides - Child Marriage Atlas Pakistan",
                        "indicator": indicator,
                        "value": value,
                        "unit": unit,
                        "geographic_scope": "Pakistan",
                        "extraction_method": "html_table",
                        "extraction_confidence": 0.8,
                        "scraped_at": now.isoformat(),
                    })

        return records

    def _extract_key_indicators(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract key indicators from structured sections.

        Looks for common patterns in child marriage atlas pages: headings
        followed by stat values, definition lists, and labeled data points.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Look for heading + value pairs (e.g., "Married by 15" followed by "3%")
        headings = soup.find_all(["h2", "h3", "h4", "h5", "dt", "strong", "b"])
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            if not heading_text:
                continue

            # Check the next sibling or parent's next element for a value
            next_el = heading.find_next_sibling()
            if not next_el:
                next_el = heading.find_next()
            if not next_el:
                continue

            next_text = next_el.get_text(strip=True)
            value = self._parse_value(next_text)
            if value is None:
                continue

            indicator = self._classify_indicator(heading_text)
            unit = "percent" if "%" in next_text else "count"

            records.append({
                "source_name": self.name,
                "report_year": self._extract_year(next_text) or now.year,
                "report_title": "Girls Not Brides - Child Marriage Atlas Pakistan",
                "indicator": indicator,
                "value": value,
                "unit": unit,
                "geographic_scope": "Pakistan",
                "extraction_method": "html_key_indicator",
                "extraction_confidence": 0.75,
                "scraped_at": now.isoformat(),
            })

        # Look for definition lists (dl > dt/dd pairs)
        for dl in soup.find_all("dl"):
            terms = dl.find_all("dt")
            definitions = dl.find_all("dd")
            for dt, dd in zip(terms, definitions):
                dt_text = dt.get_text(strip=True)
                dd_text = dd.get_text(strip=True)
                value = self._parse_value(dd_text)
                if value is None:
                    continue

                records.append({
                    "source_name": self.name,
                    "report_year": self._extract_year(dd_text) or now.year,
                    "report_title": "Girls Not Brides - Child Marriage Atlas Pakistan",
                    "indicator": self._classify_indicator(dt_text),
                    "value": value,
                    "unit": "percent" if "%" in dd_text else "count",
                    "geographic_scope": "Pakistan",
                    "extraction_method": "html_definition_list",
                    "extraction_confidence": 0.75,
                    "scraped_at": now.isoformat(),
                })

        return records

    def _extract_laws_section(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract legal framework information about child marriage laws.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records for legal indicators.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        law_keywords = [
            "law", "legal", "legislation", "minimum age",
            "prohibition", "penalty", "exception",
        ]

        for section in soup.find_all(["div", "section", "article"]):
            section_text = section.get_text(separator=" ", strip=True)
            if len(section_text) > 2000 or len(section_text) < 20:
                continue

            section_lower = section_text.lower()
            if not any(kw in section_lower for kw in law_keywords):
                continue

            # Extract minimum marriage ages
            age_pattern = re.search(
                r"(?:minimum|legal)\s+(?:age|marriageable age)[^.]*?(\d+)",
                section_text,
                re.IGNORECASE,
            )
            if age_pattern:
                records.append({
                    "source_name": self.name,
                    "report_year": now.year,
                    "report_title": "Girls Not Brides - Legal Framework Pakistan",
                    "indicator": "legal_minimum_age_marriage",
                    "value": int(age_pattern.group(1)),
                    "unit": "years",
                    "geographic_scope": "Pakistan",
                    "extraction_method": "html_law_section",
                    "extraction_confidence": 0.7,
                    "scraped_at": now.isoformat(),
                })

        return records

    async def _fetch_with_wayback_fallback(self, url: str) -> str:
        """Fetch a URL, falling back to Wayback Machine if live site fails.

        Args:
            url: Primary URL to fetch.

        Returns:
            HTML content as string.

        Raises:
            Exception: If both live and Wayback fetches fail.
        """
        try:
            response = await self.fetch(url)
            return response.text
        except Exception as live_exc:
            logger.warning(
                "[%s] Live fetch failed for %s: %s — trying Wayback Machine",
                self.name, url, live_exc,
            )
            wayback_url = f"{WAYBACK_BASE}/{url}"
            try:
                response = await self.fetch(wayback_url)
                logger.info("[%s] Successfully fetched from Wayback Machine", self.name)
                return response.text
            except Exception as wb_exc:
                logger.error(
                    "[%s] Wayback Machine fallback also failed: %s",
                    self.name, wb_exc,
                )
                raise live_exc from wb_exc

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch the Girls Not Brides Pakistan atlas page and extract data.

        Combines multiple extraction strategies: stat blocks, HTML tables,
        key indicator sections, and legal framework data. Falls back to
        Wayback Machine if the live site is unreachable.

        Returns:
            List of statistical_reports records.
        """
        logger.info("[%s] Fetching Girls Not Brides atlas: %s", self.name, self.source_url)

        html = await self._fetch_with_wayback_fallback(self.source_url)
        soup = BeautifulSoup(html, "html.parser")

        all_records: list[dict[str, Any]] = []

        # Strategy 1: Extract infographic stat blocks
        stat_records = self._extract_stat_blocks(soup)
        all_records.extend(stat_records)
        logger.info("[%s] Extracted %d stat block records", self.name, len(stat_records))

        # Strategy 2: Extract HTML tables
        table_records = self._extract_tables(soup)
        all_records.extend(table_records)
        logger.info("[%s] Extracted %d table records", self.name, len(table_records))

        # Strategy 3: Extract key indicator sections
        indicator_records = self._extract_key_indicators(soup)
        all_records.extend(indicator_records)
        logger.info("[%s] Extracted %d key indicator records", self.name, len(indicator_records))

        # Strategy 4: Extract legal framework data
        law_records = self._extract_laws_section(soup)
        all_records.extend(law_records)
        logger.info("[%s] Extracted %d law records", self.name, len(law_records))

        logger.info("[%s] Total records: %d", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Girls Not Brides statistical report record.

        Requires source_name, a non-empty indicator, and a value.

        Args:
            record: A single record dictionary.

        Returns:
            True if the record passes validation.
        """
        if not record.get("source_name"):
            return False
        if not record.get("indicator"):
            return False
        if record.get("value") is None:
            return False
        return True
