"""Digital Rights Foundation (DRF) Cyber Harassment Helpline scraper.

Scrapes helpline statistics from the DRF cyber harassment helpline
page, tracking complaint volumes (~263 complaints/month) and
categories relevant to child online exploitation.

URL: https://digitalrightsfoundation.pk/cyber-harassment-helpline/
Schedule: Monthly (0 3 1 * *)
Priority: P2
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin
import re

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_html_scraper import BaseHTMLTableScraper

logger = logging.getLogger(__name__)

_YEAR_PATTERN = re.compile(r"20[12]\d")
_NUMBER_PATTERN = re.compile(r"([\d,]+)")

# Categories relevant to child exploitation from DRF helpline
_RELEVANT_CATEGORIES: list[str] = [
    "child",
    "minor",
    "sextortion",
    "blackmail",
    "non-consensual",
    "image abuse",
    "harassment",
    "stalking",
    "impersonation",
    "defamation",
    "hate speech",
    "cyber bullying",
    "cyberbullying",
    "online abuse",
    "pornograph",
    "sexual",
    "grooming",
]


class DRFNewslettersScraper(BaseHTMLTableScraper):
    """Scraper for DRF Cyber Harassment Helpline statistics.

    Extracts helpline complaint data from DRF's helpline page
    and linked newsletters/reports. Captures complaint volumes,
    category breakdowns, and demographic information relevant
    to child online exploitation in Pakistan.
    """

    name: str = "drf_newsletters"
    source_url: str = (
        "https://digitalrightsfoundation.pk/cyber-harassment-helpline/"
    )
    schedule: str = "0 3 1 * *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0

    def _parse_numeric(self, text: str) -> float | None:
        """Parse a numeric value from text, handling commas."""
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None
        if cleaned.endswith("%"):
            try:
                return float(cleaned[:-1])
            except ValueError:
                return None
        try:
            return float(cleaned) if "." in cleaned else float(int(cleaned))
        except ValueError:
            return None

    def _extract_year(self, text: str) -> int | None:
        """Extract a year from text."""
        match = _YEAR_PATTERN.search(text)
        return int(match.group()) if match else None

    def _is_relevant_category(self, text: str) -> bool:
        """Check if a category is relevant to child online exploitation."""
        text_lower = text.lower()
        return any(cat in text_lower for cat in _RELEVANT_CATEGORIES)

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the DRF helpline scraping pipeline.

        Fetches the main helpline page, extracts statistics from
        tables and text, then follows links to newsletters/reports
        for additional data.
        """
        all_records: list[dict[str, Any]] = []

        # 1. Fetch main helpline page
        try:
            response = await self.fetch(self.source_url)
            main_html = response.text

            # Extract tables from main page
            table_records = self._extract_table_data(main_html)
            all_records.extend(table_records)

            # Extract inline statistics from text
            text_records = self._extract_text_stats(main_html)
            all_records.extend(text_records)

            # Find newsletter/report links to follow
            newsletter_links = self._find_newsletter_links(main_html)
            for link_url in newsletter_links:
                try:
                    nl_response = await self.fetch(link_url)
                    nl_records = self._extract_newsletter_data(
                        nl_response.text, link_url
                    )
                    all_records.extend(nl_records)
                except Exception as exc:
                    logger.warning(
                        "[%s] Failed to fetch newsletter %s: %s",
                        self.name, link_url, exc,
                    )
        except Exception as exc:
            logger.error("[%s] Failed to fetch main page: %s", self.name, exc)

        return all_records

    def _extract_table_data(self, html: str) -> list[dict[str, Any]]:
        """Extract helpline statistics from HTML tables."""
        tables = self.extract_tables(html)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        for table in tables:
            for row in table:
                # Find the indicator/category column
                indicator = ""
                value = None
                unit = "complaints"

                for key, val_str in row.items():
                    parsed = self._parse_numeric(val_str)
                    if parsed is not None:
                        value = parsed
                        if "%" in val_str:
                            unit = "percent"
                    elif val_str and not indicator:
                        indicator = val_str.strip()

                if indicator and value is not None:
                    records.append({
                        "source_name": "Digital Rights Foundation",
                        "report_year": self._extract_year(html),
                        "report_title": "DRF Cyber Harassment Helpline Report",
                        "indicator": indicator,
                        "value": value,
                        "unit": unit,
                        "geographic_scope": "Pakistan",
                        "pdf_url": None,
                        "extraction_method": "html_table",
                        "scraped_at": now,
                    })

        return records

    def _extract_text_stats(self, html: str) -> list[dict[str, Any]]:
        """Extract inline statistics mentioned in page text."""
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ")
        now = datetime.now(timezone.utc).isoformat()
        report_year = self._extract_year(text)
        records: list[dict[str, Any]] = []

        patterns = {
            "Total Complaints Received": [
                r"(\d[\d,]+)\s*(?:total\s+)?complaints?\s*(?:received|registered)",
                r"received\s+(\d[\d,]+)\s*complaints?",
                r"helpline.*?(\d[\d,]+)\s*complaints?",
            ],
            "Monthly Average Complaints": [
                r"(\d[\d,]+)\s*complaints?\s*(?:per\s+)?month",
                r"average\s*(?:of\s+)?(\d[\d,]+)\s*complaints?",
                r"monthly\s*average.*?(\d[\d,]+)",
            ],
            "Female Complainants": [
                r"(\d[\d,]+)%?\s*(?:female|women)\s*complainants?",
                r"(?:female|women).*?(\d[\d,]+)\s*%",
            ],
            "Minor Victims": [
                r"(\d[\d,]+)\s*(?:minor|child|underage)\s*victims?",
                r"(?:minor|child).*?(\d[\d,]+)\s*(?:complaints?|cases?)",
            ],
            "Sextortion Cases": [
                r"(\d[\d,]+)\s*sextortion",
                r"sextortion.*?(\d[\d,]+)",
            ],
            "Online Harassment Cases": [
                r"(\d[\d,]+)\s*(?:online\s+)?harassment",
                r"harassment.*?(\d[\d,]+)",
            ],
            "Image-Based Abuse Cases": [
                r"(\d[\d,]+)\s*(?:image[- ]based\s+)?(?:abuse|NCII)",
                r"non[- ]consensual.*?(\d[\d,]+)",
            ],
        }

        for indicator, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = self._parse_numeric(match.group(1))
                    if value is not None:
                        unit = "percent" if "%" in match.group(0) else "complaints"
                        records.append({
                            "source_name": "Digital Rights Foundation",
                            "report_year": report_year,
                            "report_title": "DRF Cyber Harassment Helpline Report",
                            "indicator": indicator,
                            "value": value,
                            "unit": unit,
                            "geographic_scope": "Pakistan",
                            "pdf_url": None,
                            "extraction_method": "text_regex",
                            "scraped_at": now,
                        })
                        break

        return records

    def _find_newsletter_links(self, html: str) -> list[str]:
        """Find links to DRF newsletters and reports on the page."""
        links = self.extract_links(
            html,
            r"newsletter|report|publication|helpline.*report|annual.*report"
        )
        urls: list[str] = []
        seen: set[str] = set()

        for link in links:
            href = link.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = urljoin(self.source_url, href)
            if href not in seen:
                seen.add(href)
                urls.append(href)

        return urls

    def _extract_newsletter_data(
        self, html: str, url: str
    ) -> list[dict[str, Any]]:
        """Extract statistics from a linked newsletter/report page."""
        tables = self.extract_tables(html)
        now = datetime.now(timezone.utc).isoformat()
        report_year = self._extract_year(html)
        records: list[dict[str, Any]] = []

        for table in tables:
            for row in table:
                indicator = ""
                value = None
                unit = "complaints"

                for key, val_str in row.items():
                    parsed = self._parse_numeric(val_str)
                    if parsed is not None:
                        value = parsed
                        if "%" in val_str:
                            unit = "percent"
                    elif val_str and not indicator:
                        indicator = val_str.strip()

                if indicator and value is not None:
                    records.append({
                        "source_name": "Digital Rights Foundation",
                        "report_year": report_year,
                        "report_title": "DRF Newsletter / Report",
                        "indicator": indicator,
                        "value": value,
                        "unit": unit,
                        "geographic_scope": "Pakistan",
                        "pdf_url": url if url.endswith(".pdf") else None,
                        "extraction_method": "html_table",
                        "scraped_at": now,
                    })

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a statistical_reports record from DRF.

        Requires source_name and indicator at minimum.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
            and record.get("geographic_scope")
        )
