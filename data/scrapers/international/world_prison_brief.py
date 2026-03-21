"""World Prison Brief scraper for Pakistan prison statistics.

Scrapes the Prison Studies country page for Pakistan to extract
prison population statistics, juvenile prisoner percentages,
pretrial detainee rates, and related criminal justice indicators.

Source: https://www.prisonstudies.org/country/pakistan
Schedule: Annually (0 2 15 1 *)
Priority: P2 — Supplementary incarceration statistics
"""

from datetime import datetime, timezone
from typing import Any

import logging
import re

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

COUNTRY_URL: str = "https://www.prisonstudies.org/country/pakistan"

# Key facts to extract from the country page
TARGET_INDICATORS: dict[str, list[str]] = {
    "prison_population_total": [
        "prison population total",
        "total prison population",
    ],
    "prison_population_rate": [
        "prison population rate",
        "per 100,000",
    ],
    "pretrial_detainees_pct": [
        "pre-trial detainees",
        "remand prisoners",
    ],
    "female_prisoners_pct": [
        "female prisoners",
        "percentage of female",
        "women prisoners",
    ],
    "juveniles_prisoners_pct": [
        "juveniles",
        "minors",
        "young prisoners",
        "juvenile prisoners",
    ],
    "occupancy_level": [
        "occupancy level",
        "occupancy rate",
        "overcrowding",
    ],
    "official_capacity": [
        "official capacity",
        "prison capacity",
    ],
    "number_of_establishments": [
        "number of establishments",
        "number of prisons",
    ],
}


class WorldPrisonBriefScraper(BaseScraper):
    """Scraper for World Prison Brief — Pakistan prison statistics.

    Fetches the Pakistan country page from prisonstudies.org, parses
    the key fact boxes and data tables using BeautifulSoup, and
    extracts prison population metrics into statistical_reports format.
    """

    name: str = "world_prison_brief"
    source_url: str = "https://www.prisonstudies.org/country/pakistan"
    schedule: str = "0 2 15 1 *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0
    request_timeout: float = 30.0

    async def _fetch_country_page(self) -> str | None:
        """Fetch the Pakistan country page HTML.

        Returns:
            HTML content string, or None on failure.
        """
        try:
            response = await self.fetch(COUNTRY_URL)
            return response.text
        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch country page: %s", self.name, exc
            )
            return None

    @staticmethod
    def _parse_key_facts(html: str) -> list[dict[str, str]]:
        """Extract key fact entries from the country page HTML.

        Parses both dedicated fact box elements and generic data tables
        to capture all statistical indicators on the page.

        Args:
            html: Raw HTML content of the country page.

        Returns:
            List of dicts with 'label' and 'value' keys.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup (bs4) is required for World Prison Brief scraper")
            return []

        soup = BeautifulSoup(html, "html.parser")
        facts: list[dict[str, str]] = []

        # Strategy 1: Look for field-label / field-item pairs (Drupal-style)
        for field in soup.find_all(class_=re.compile(r"field--name")):
            label_el = field.find(class_=re.compile(r"field__label|field-label"))
            value_el = field.find(class_=re.compile(r"field__item|field-item"))
            if label_el and value_el:
                facts.append({
                    "label": label_el.get_text(strip=True),
                    "value": value_el.get_text(strip=True),
                })

        # Strategy 2: Look for definition lists
        for dl in soup.find_all("dl"):
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for dt, dd in zip(dts, dds):
                facts.append({
                    "label": dt.get_text(strip=True),
                    "value": dd.get_text(strip=True),
                })

        # Strategy 3: Look for table rows with two cells (label-value pattern)
        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                cells = tr.find_all(["th", "td"])
                if len(cells) == 2:
                    facts.append({
                        "label": cells[0].get_text(strip=True),
                        "value": cells[1].get_text(strip=True),
                    })

        # Strategy 4: Look for common wrapper divs with strong/span patterns
        for div in soup.find_all(["div", "li", "p"]):
            strong = div.find("strong")
            if strong:
                label = strong.get_text(strip=True).rstrip(":")
                # Value is the remaining text after the strong tag
                full_text = div.get_text(strip=True)
                value = full_text.replace(strong.get_text(strip=True), "").strip().lstrip(":")
                if label and value:
                    facts.append({"label": label, "value": value.strip()})

        logger.info("Extracted %d raw fact entries from page", len(facts))
        return facts

    def _match_indicator(self, label: str) -> str | None:
        """Match a fact label to a known indicator code.

        Args:
            label: Label text from the page.

        Returns:
            Indicator code string, or None if no match.
        """
        label_lower = label.lower()
        for indicator_code, patterns in TARGET_INDICATORS.items():
            if any(pattern in label_lower for pattern in patterns):
                return indicator_code
        return None

    @staticmethod
    def _parse_numeric_value(text: str) -> float | None:
        """Parse a numeric value from fact text, handling commas and %.

        Args:
            text: Raw value text (e.g., "77,275", "68.4%", "117.9%").

        Returns:
            Parsed float, or None if parsing fails.
        """
        cleaned = text.strip()
        # Remove parenthetical notes like "(based on...)"
        cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
        # Remove trailing text after the number
        match = re.match(r"^[\d,]+\.?\d*%?", cleaned)
        if not match:
            return None
        num_str = match.group(0).replace(",", "").replace("%", "")
        try:
            return float(num_str)
        except ValueError:
            return None

    @staticmethod
    def _determine_unit(indicator_code: str, raw_value: str) -> str:
        """Determine the unit of measurement for an indicator.

        Args:
            indicator_code: Matched indicator code.
            raw_value: Raw value text for context.

        Returns:
            Unit string: "percent", "rate_per_100k", or "count".
        """
        if "pct" in indicator_code or "%" in raw_value:
            return "percent"
        if "rate" in indicator_code:
            return "rate_per_100k"
        return "count"

    @staticmethod
    def _extract_data_year(html: str) -> str | None:
        """Extract the data reference year from the page HTML.

        Looks for patterns like "as of December 2023" or "(2022)" in
        the page content.

        Args:
            html: Raw HTML content.

        Returns:
            Year string, or None if not found.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return None

        soup = BeautifulSoup(html, "html.parser")
        page_text = soup.get_text()

        # Look for date references near data
        patterns = [
            r"(?:as of|date of|updated|data from)[^\d]*((?:19|20)\d{2})",
            r"\b((?:19|20)\d{2})\s*(?:\)|data|\.|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _build_records(
        self,
        facts: list[dict[str, str]],
        data_year: str | None,
    ) -> list[dict[str, Any]]:
        """Convert matched facts into statistical_reports records.

        Args:
            facts: Parsed label-value pairs from the page.
            data_year: Reference year for the data, if found.

        Returns:
            List of formatted record dicts.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()
        seen_indicators: set[str] = set()

        for fact in facts:
            indicator_code = self._match_indicator(fact["label"])
            if indicator_code is None:
                continue

            # Skip duplicates — take only the first match per indicator
            if indicator_code in seen_indicators:
                continue

            value = self._parse_numeric_value(fact["value"])
            if value is None:
                continue

            seen_indicators.add(indicator_code)
            unit = self._determine_unit(indicator_code, fact["value"])
            label_display = fact["label"].strip().rstrip(":")

            records.append({
                "source_name": "world_prison_brief",
                "report_year": data_year,
                "report_title": (
                    f"World Prison Brief — {label_display} — "
                    f"Pakistan {data_year or 'N/A'}"
                ),
                "indicator": indicator_code,
                "indicator_label": label_display,
                "value": value,
                "unit": unit,
                "geographic_scope": "Pakistan",
                "pdf_url": None,
                "extraction_method": "html_scrape",
                "extraction_confidence": 0.80,
                "source_page": COUNTRY_URL,
                "scraped_at": now,
            })

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the World Prison Brief scraping pipeline.

        Fetches the Pakistan country page, extracts key facts and
        data tables, matches them to target indicators, and returns
        statistical_reports formatted records.

        Returns:
            List of statistical_reports records for Pakistan prison
            and juvenile detention statistics.
        """
        html = await self._fetch_country_page()
        if html is None:
            return []

        facts = self._parse_key_facts(html)
        if not facts:
            logger.warning("[%s] No facts extracted from page", self.name)
            return []

        data_year = self._extract_data_year(html)
        if data_year:
            logger.info("[%s] Detected data year: %s", self.name, data_year)

        records = self._build_records(facts, data_year)
        logger.info(
            "[%s] Produced %d records from %d fact entries",
            self.name, len(records), len(facts),
        )
        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a World Prison Brief statistical_reports record.

        Requires source_name, indicator, and a numeric value.
        Report year is optional since the page may not always
        specify a date.
        """
        if not record.get("source_name"):
            return False
        if not record.get("indicator"):
            return False
        if record.get("value") is None:
            return False
        return True
