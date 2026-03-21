"""End Corporal Punishment Initiative — Pakistan country report scraper.

Scrapes the End Corporal Punishment Initiative's Pakistan page for
legal status tables, reform progress, and prohibition status across
different settings (home, school, alternative care, penal system,
sentence for crime).

URL: https://endcorporalpunishment.org/reports-on-every-state-and-territory/pakistan/
Schedule: Annually (0 0 1 3 *)
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

# Settings where corporal punishment legality is tracked
CP_SETTINGS: list[str] = [
    "home",
    "alternative_care",
    "day_care",
    "schools",
    "penal_institutions",
    "sentence_for_crime",
]

# Indicators tracked on corporal punishment country pages
CP_INDICATORS: list[str] = [
    "prohibition_status_home",
    "prohibition_status_schools",
    "prohibition_status_penal",
    "prohibition_status_alternative_care",
    "prohibition_status_day_care",
    "prohibition_status_sentence_for_crime",
    "reform_progress",
    "legal_framework_score",
    "crc_recommendations",
    "upr_recommendations",
]


class CorporalPunishmentScraper(BaseScraper):
    """Scraper for End Corporal Punishment Initiative — Pakistan.

    Parses the Pakistan country page for legality status tables
    showing prohibition status in each setting, reform progress
    indicators, and international recommendations (CRC, UPR).
    Falls back to Wayback Machine if live site is unreachable.
    """

    name: str = "corporal_punishment"
    source_url: str = (
        "https://endcorporalpunishment.org/"
        "reports-on-every-state-and-territory/pakistan/"
    )
    schedule: str = "0 0 1 3 *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0

    def _classify_setting(self, text: str) -> str:
        """Map raw text to a standardized setting identifier.

        Args:
            text: Raw text describing a setting or context.

        Returns:
            Standardized setting name.
        """
        text_lower = text.lower()

        mapping: dict[str, list[str]] = {
            "home": ["home", "family", "domestic", "household"],
            "schools": ["school", "education", "classroom", "teacher"],
            "penal_institutions": [
                "penal", "prison", "detention", "correctional",
                "juvenile detention", "custody",
            ],
            "alternative_care": [
                "alternative care", "foster", "institutional care",
                "residential care", "care setting",
            ],
            "day_care": ["day care", "daycare", "childcare", "early childhood"],
            "sentence_for_crime": [
                "sentence", "judicial", "court", "criminal",
                "lawful sentence", "sentence for crime",
            ],
        }

        for setting, keywords in mapping.items():
            if any(kw in text_lower for kw in keywords):
                return setting

        return text.strip()[:80]

    def _parse_prohibition_status(self, text: str) -> str:
        """Parse the prohibition status from text.

        Args:
            text: Text describing legality or prohibition status.

        Returns:
            One of: 'prohibited', 'not_prohibited', 'partially_prohibited', 'unknown'.
        """
        text_lower = text.lower().strip()

        if any(kw in text_lower for kw in [
            "prohibited", "full prohibition", "fully prohibited",
            "unlawful", "banned",
        ]):
            if any(kw in text_lower for kw in ["not prohibited", "not yet", "no prohibition"]):
                return "not_prohibited"
            return "prohibited"

        if any(kw in text_lower for kw in [
            "not prohibited", "lawful", "no prohibition",
            "not fully", "legal", "no explicit",
        ]):
            return "not_prohibited"

        if any(kw in text_lower for kw in [
            "partial", "some", "limited", "incomplete",
        ]):
            return "partially_prohibited"

        return "unknown"

    def _extract_status_table(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract legality status from HTML tables.

        The End Corporal Punishment site typically presents a table
        with settings (home, school, etc.) and their prohibition status.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if not rows:
                continue

            # Extract headers
            header_row = rows[0]
            [
                cell.get_text(strip=True).lower()
                for cell in header_row.find_all(["th", "td"])
            ]

            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not cells or len(cells) < 2:
                    continue

                setting_text = cells[0]
                setting = self._classify_setting(setting_text)
                status_text = cells[1] if len(cells) > 1 else ""
                status = self._parse_prohibition_status(status_text)

                # Encode status as a numeric value for statistical_reports
                status_value_map = {
                    "prohibited": 1,
                    "partially_prohibited": 0.5,
                    "not_prohibited": 0,
                    "unknown": -1,
                }

                records.append({
                    "source_name": self.name,
                    "report_year": now.year,
                    "report_title": (
                        "End Corporal Punishment - Pakistan Legal Status"
                    ),
                    "indicator": f"prohibition_status_{setting}",
                    "value": status_value_map.get(status, -1),
                    "unit": "prohibition_status",
                    "geographic_scope": "Pakistan",
                    "extraction_method": "html_table",
                    "extraction_confidence": 0.85,
                    "status_label": status,
                    "setting": setting,
                    "raw_status_text": status_text,
                    "scraped_at": now.isoformat(),
                })

                # If there are additional columns (e.g., year of reform, notes)
                if len(cells) > 2:
                    for i, extra_cell in enumerate(cells[2:], start=2):
                        extra_text = extra_cell.strip()
                        if not extra_text:
                            continue

                        year = self._extract_year(extra_text)
                        if year:
                            records.append({
                                "source_name": self.name,
                                "report_year": year,
                                "report_title": (
                                    "End Corporal Punishment - Pakistan Reform Year"
                                ),
                                "indicator": f"reform_year_{setting}",
                                "value": year,
                                "unit": "year",
                                "geographic_scope": "Pakistan",
                                "extraction_method": "html_table",
                                "extraction_confidence": 0.7,
                                "setting": setting,
                                "scraped_at": now.isoformat(),
                            })

        return records

    def _extract_year(self, text: str) -> int | None:
        """Extract a four-digit year from text.

        Args:
            text: Text to search for a year.

        Returns:
            Year as integer or None.
        """
        year_match = re.search(r"(19|20)\d{2}", text)
        if year_match:
            return int(year_match.group())
        return None

    def _extract_section_stats(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract statistics from structured page sections.

        Looks for headings identifying settings followed by status
        descriptions, and for structured lists of legal provisions.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Pattern: heading followed by status text
        setting_keywords = [
            "home", "school", "penal", "alternative care",
            "day care", "sentence for crime",
        ]

        for heading in soup.find_all(["h2", "h3", "h4", "h5"]):
            heading_text = heading.get_text(strip=True)
            heading_lower = heading_text.lower()

            matched_setting = None
            for kw in setting_keywords:
                if kw in heading_lower:
                    matched_setting = self._classify_setting(heading_text)
                    break

            if not matched_setting:
                continue

            # Collect text from subsequent siblings until the next heading
            description_parts: list[str] = []
            sibling = heading.find_next_sibling()
            while sibling and sibling.name not in ["h2", "h3", "h4", "h5"]:
                sibling_text = sibling.get_text(strip=True)
                if sibling_text:
                    description_parts.append(sibling_text)
                sibling = sibling.find_next_sibling()

            full_text = " ".join(description_parts)
            if not full_text:
                continue

            status = self._parse_prohibition_status(full_text)
            status_value_map = {
                "prohibited": 1,
                "partially_prohibited": 0.5,
                "not_prohibited": 0,
                "unknown": -1,
            }

            records.append({
                "source_name": self.name,
                "report_year": self._extract_year(full_text) or now.year,
                "report_title": (
                    "End Corporal Punishment - Pakistan Section Data"
                ),
                "indicator": f"prohibition_status_{matched_setting}",
                "value": status_value_map.get(status, -1),
                "unit": "prohibition_status",
                "geographic_scope": "Pakistan",
                "extraction_method": "html_section",
                "extraction_confidence": 0.65,
                "status_label": status,
                "setting": matched_setting,
                "scraped_at": now.isoformat(),
            })

        return records

    def _extract_recommendations(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract CRC and UPR recommendations counts.

        Looks for sections mentioning Committee on the Rights of the Child
        (CRC) or Universal Periodic Review (UPR) recommendations.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        page_text = soup.get_text(separator=" ", strip=True)

        recommendation_patterns = [
            (r"CRC[^.]*?(\d+)\s*recommend", "crc_recommendations"),
            (r"UPR[^.]*?(\d+)\s*recommend", "upr_recommendations"),
            (r"(\d+)\s*CRC\s*recommend", "crc_recommendations"),
            (r"(\d+)\s*UPR\s*recommend", "upr_recommendations"),
            (r"Committee on the Rights of the Child[^.]*?(\d+)", "crc_recommendations"),
            (r"Universal Periodic Review[^.]*?(\d+)", "upr_recommendations"),
        ]

        seen_indicators: set[str] = set()
        for pattern, indicator in recommendation_patterns:
            if indicator in seen_indicators:
                continue
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                seen_indicators.add(indicator)
                try:
                    value = int(match.group(1))
                except ValueError:
                    continue

                records.append({
                    "source_name": self.name,
                    "report_year": self._extract_year(page_text) or now.year,
                    "report_title": (
                        "End Corporal Punishment - International Recommendations"
                    ),
                    "indicator": indicator,
                    "value": value,
                    "unit": "recommendations",
                    "geographic_scope": "Pakistan",
                    "extraction_method": "html_text_pattern",
                    "extraction_confidence": 0.6,
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
                logger.info(
                    "[%s] Successfully fetched from Wayback Machine", self.name,
                )
                return response.text
            except Exception as wb_exc:
                logger.error(
                    "[%s] Wayback Machine fallback also failed: %s",
                    self.name, wb_exc,
                )
                raise live_exc from wb_exc

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch the End Corporal Punishment Pakistan page and extract data.

        Combines multiple extraction strategies: legality status tables,
        section-based parsing, and recommendation counts. Falls back to
        Wayback Machine if the live site is unreachable.

        Returns:
            List of statistical_reports records.
        """
        logger.info(
            "[%s] Fetching End Corporal Punishment page: %s",
            self.name, self.source_url,
        )

        html = await self._fetch_with_wayback_fallback(self.source_url)
        soup = BeautifulSoup(html, "html.parser")

        all_records: list[dict[str, Any]] = []

        # Strategy 1: Extract legality status tables
        table_records = self._extract_status_table(soup)
        all_records.extend(table_records)
        logger.info(
            "[%s] Extracted %d status table records", self.name, len(table_records),
        )

        # Strategy 2: Extract section-based stats
        section_records = self._extract_section_stats(soup)
        all_records.extend(section_records)
        logger.info(
            "[%s] Extracted %d section records", self.name, len(section_records),
        )

        # Strategy 3: Extract CRC/UPR recommendations
        rec_records = self._extract_recommendations(soup)
        all_records.extend(rec_records)
        logger.info(
            "[%s] Extracted %d recommendation records", self.name, len(rec_records),
        )

        logger.info("[%s] Total records: %d", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a corporal punishment statistical report record.

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
