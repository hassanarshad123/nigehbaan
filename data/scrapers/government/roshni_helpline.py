"""Roshni Helpline missing children recovery statistics scraper.

Scrapes the Roshni Helpline website for missing children recovery
statistics, annual report data, and case counts. Checks multiple
pages including the homepage, statistics pages, and report links.
Falls back to Wayback Machine if the live site is unreachable.

URL: https://roshnihelpline.org/
Schedule: Quarterly (0 3 1 */3 *)
Priority: P1
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

# Known sub-pages on the Roshni Helpline site that may contain data
ROSHNI_DATA_PAGES: list[str] = [
    "https://roshnihelpline.org/",
    "https://roshnihelpline.org/statistics",
    "https://roshnihelpline.org/stats",
    "https://roshnihelpline.org/reports",
    "https://roshnihelpline.org/annual-report",
    "https://roshnihelpline.org/about",
    "https://roshnihelpline.org/achievements",
    "https://roshnihelpline.org/our-work",
    "https://roshnihelpline.org/impact",
]

# Indicators tracked from Roshni Helpline data
ROSHNI_INDICATORS: list[str] = [
    "missing_children_reported",
    "missing_children_recovered",
    "recovery_rate",
    "total_calls_received",
    "helpline_cases_registered",
    "children_reunited",
    "fir_registered",
    "counseling_sessions",
    "awareness_sessions",
    "districts_covered",
]


class RoshniHelplineScraper(BaseScraper):
    """Scraper for Roshni Helpline missing children recovery statistics.

    Crawls the Roshni Helpline website and sub-pages to extract
    recovery statistics, annual report data, and PDF report links.
    Uses multiple extraction strategies including stat blocks, tables,
    and PDF link discovery. Falls back to Wayback Machine if the
    live site is unreachable.
    """

    name: str = "roshni_helpline"
    source_url: str = "https://roshnihelpline.org/"
    schedule: str = "0 3 1 */3 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    def _classify_indicator(self, text: str) -> str:
        """Map raw text to a standardized Roshni indicator.

        Args:
            text: Raw text from page element.

        Returns:
            Standardized indicator name.
        """
        text_lower = text.lower()

        mapping: dict[str, list[str]] = {
            "missing_children_reported": [
                "missing children reported", "children reported missing",
                "reported missing", "missing cases",
            ],
            "missing_children_recovered": [
                "recovered", "found", "reunited", "traced",
                "children recovered", "recovery",
            ],
            "recovery_rate": [
                "recovery rate", "success rate", "rate of recovery",
            ],
            "total_calls_received": [
                "calls received", "total calls", "helpline calls",
                "phone calls", "call volume",
            ],
            "helpline_cases_registered": [
                "cases registered", "registered cases", "case registration",
            ],
            "children_reunited": [
                "reunited", "reunification", "returned to family",
                "handed over", "restored",
            ],
            "fir_registered": [
                "fir", "first information report", "police report",
                "firs registered", "fir lodged",
            ],
            "counseling_sessions": [
                "counseling", "counselling", "psychosocial",
                "therapy", "mental health",
            ],
            "awareness_sessions": [
                "awareness", "campaign", "outreach", "training",
                "sensitization",
            ],
            "districts_covered": [
                "district", "coverage", "areas covered",
                "geographic coverage",
            ],
        }

        for indicator, keywords in mapping.items():
            if any(kw in text_lower for kw in keywords):
                return indicator

        return text.strip()[:100]

    def _parse_value(self, text: str) -> float | int | None:
        """Parse a numeric value from text.

        Handles percentages, commas, plus signs, and multiplier words.

        Args:
            text: Raw text potentially containing a number.

        Returns:
            Numeric value or None.
        """
        cleaned = (
            text.strip()
            .replace(",", "")
            .replace("%", "")
            .replace("+", "")
            .replace(" ", "")
        )
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
        """Extract statistics from counter/stat blocks on the page.

        NGO websites commonly display impact stats in prominent
        counter blocks (e.g., "5,000+ Children Recovered").

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Patterns for counter/stat blocks
        stat_patterns = [
            r"(\d[\d,+.]*)\s*\+?\s*(?:children|child|kids?)\s+(?:recovered|found|reunited|traced)",
            r"(\d[\d,+.]*)\s*\+?\s*(?:missing)\s+(?:children|child|cases?)",
            r"(\d[\d,+.]*)\s*\+?\s*(?:calls?|helpline)\s+(?:received|answered)",
            r"(\d[\d,+.]*)\s*\+?\s*(?:cases?)\s+(?:registered|handled|resolved)",
            r"(\d[\d,+.]*)\s*\+?\s*(?:FIRs?)\s+(?:registered|lodged|filed)",
            r"(\d[\d,+.]*)\s*(%)\s*(?:recovery|success)\s+rate",
            r"(?:recovered|found|reunited|traced)\s+(\d[\d,+.]*)\s*\+?\s*(?:children|child)",
        ]

        for block in soup.find_all(["div", "section", "span", "li", "p", "h2", "h3"]):
            text = block.get_text(separator=" ", strip=True)
            if not text or len(text) > 500:
                continue

            for pattern in stat_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if not match:
                    continue

                raw_value = match.group(1).replace(",", "").replace("+", "")
                try:
                    value: float | int = (
                        float(raw_value) if "." in raw_value else int(raw_value)
                    )
                except ValueError:
                    continue

                unit = "count"
                if len(match.groups()) > 1 and match.group(2) == "%":
                    unit = "percent"

                indicator = self._classify_indicator(text[:300])

                records.append({
                    "source_name": self.name,
                    "report_year": self._extract_year(text) or now.year,
                    "report_title": "Roshni Helpline - Website Statistics",
                    "indicator": indicator,
                    "value": value,
                    "unit": unit,
                    "geographic_scope": "Pakistan",
                    "extraction_method": "html_stat_block",
                    "extraction_confidence": 0.7,
                    "scraped_at": now.isoformat(),
                })
                break  # One match per block

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

                # First cell is usually the indicator/category
                indicator_text = cells[0]
                indicator = self._classify_indicator(indicator_text)

                for i, cell_text in enumerate(cells[1:], start=1):
                    value = self._parse_value(cell_text)
                    if value is None:
                        continue

                    unit = "percent" if "%" in cell_text else "count"

                    # Try to extract year from header
                    report_year = now.year
                    if i < len(headers):
                        header_year = self._extract_year(headers[i])
                        if header_year:
                            report_year = header_year

                    records.append({
                        "source_name": self.name,
                        "report_year": report_year,
                        "report_title": "Roshni Helpline - Data Table",
                        "indicator": indicator,
                        "value": value,
                        "unit": unit,
                        "geographic_scope": "Pakistan",
                        "extraction_method": "html_table",
                        "extraction_confidence": 0.8,
                        "scraped_at": now.isoformat(),
                    })

        return records

    def _extract_counter_elements(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract data from CSS counter/odometer elements.

        Many NGO sites use JavaScript counter widgets with data attributes
        or specific CSS classes to display impact numbers.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Look for elements with counter-related classes or data attributes
        counter_selectors = [
            {"class_": re.compile(r"counter|count|number|stat|odometer|timer", re.IGNORECASE)},
            {"attrs": {"data-count": True}},
            {"attrs": {"data-target": True}},
            {"attrs": {"data-val": True}},
            {"attrs": {"data-value": True}},
        ]

        for selector in counter_selectors:
            for el in soup.find_all(**selector):
                # Try data attributes first
                value_str = (
                    el.get("data-count")
                    or el.get("data-target")
                    or el.get("data-val")
                    or el.get("data-value")
                    or el.get_text(strip=True)
                )
                if not value_str:
                    continue

                value = self._parse_value(str(value_str))
                if value is None:
                    continue

                # Get surrounding context for indicator classification
                parent = el.parent
                context_text = parent.get_text(separator=" ", strip=True) if parent else ""
                if not context_text:
                    context_text = el.get_text(strip=True)

                indicator = self._classify_indicator(context_text[:300])

                records.append({
                    "source_name": self.name,
                    "report_year": now.year,
                    "report_title": "Roshni Helpline - Counter Widget",
                    "indicator": indicator,
                    "value": value,
                    "unit": "count",
                    "geographic_scope": "Pakistan",
                    "extraction_method": "html_counter_widget",
                    "extraction_confidence": 0.65,
                    "scraped_at": now.isoformat(),
                })

        return records

    def _discover_pdf_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Discover links to PDF reports on the page.

        Args:
            soup: Parsed HTML tree.
            base_url: Base URL for resolving relative links.

        Returns:
            List of absolute PDF URLs.
        """
        pdf_urls: list[str] = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            link_text = link.get_text(strip=True).lower()

            is_pdf = href.lower().endswith(".pdf")
            mentions_report = any(
                kw in link_text
                for kw in ["report", "annual", "statistics", "data", "download", "pdf"]
            )

            if is_pdf or mentions_report:
                # Resolve relative URLs
                if href.startswith("/"):
                    href = base_url.rstrip("/") + href
                elif not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href

                pdf_urls.append(href)

        return pdf_urls

    def _extract_inline_numbers(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract standalone numbers with contextual labels.

        Scans for large numbers displayed prominently alongside
        descriptive text — common in NGO impact sections.

        Args:
            soup: Parsed HTML tree.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Look for large standalone numbers
        for el in soup.find_all(["span", "strong", "b", "h1", "h2", "h3"]):
            text = el.get_text(strip=True)

            # Match large numbers (100+) that might be impact stats
            if not re.match(r"^[\d,+.]+$", text.replace(" ", "")):
                continue

            value = self._parse_value(text)
            if value is None or (isinstance(value, (int, float)) and value < 10):
                continue

            # Get context from parent and siblings
            parent = el.parent
            if not parent:
                continue

            context = parent.get_text(separator=" ", strip=True)
            if len(context) < 5 or len(context) > 500:
                continue

            # Only include if context mentions children, helpline, or recovery
            context_lower = context.lower()
            relevant_keywords = [
                "child", "missing", "recover", "helpline", "call",
                "case", "fir", "reunite", "found", "traced",
            ]
            if not any(kw in context_lower for kw in relevant_keywords):
                continue

            indicator = self._classify_indicator(context[:300])

            records.append({
                "source_name": self.name,
                "report_year": self._extract_year(context) or now.year,
                "report_title": "Roshni Helpline - Inline Number",
                "indicator": indicator,
                "value": value,
                "unit": "count",
                "geographic_scope": "Pakistan",
                "extraction_method": "html_inline_number",
                "extraction_confidence": 0.6,
                "scraped_at": now.isoformat(),
            })

        return records

    async def _fetch_with_wayback_fallback(self, url: str) -> str | None:
        """Fetch a URL, falling back to Wayback Machine if live site fails.

        Args:
            url: Primary URL to fetch.

        Returns:
            HTML content as string, or None if all attempts fail.
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
                    "[%s] Successfully fetched %s from Wayback Machine",
                    self.name, url,
                )
                return response.text
            except Exception as wb_exc:
                logger.error(
                    "[%s] Wayback Machine fallback also failed for %s: %s",
                    self.name, url, wb_exc,
                )
                return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch Roshni Helpline pages and extract recovery statistics.

        Crawls the homepage and known sub-pages, applying multiple
        extraction strategies. Discovers and records PDF report links
        for potential downstream processing. Falls back to Wayback
        Machine for pages that fail to load.

        Returns:
            List of statistical_reports records.
        """
        logger.info(
            "[%s] Starting Roshni Helpline scrape: %s", self.name, self.source_url,
        )

        all_records: list[dict[str, Any]] = []
        all_pdf_links: list[str] = []
        now = datetime.now(timezone.utc)

        for page_url in ROSHNI_DATA_PAGES:
            html = await self._fetch_with_wayback_fallback(page_url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Strategy 1: Stat blocks with text patterns
            stat_records = self._extract_stat_blocks(soup)
            all_records.extend(stat_records)

            # Strategy 2: HTML tables
            table_records = self._extract_tables(soup)
            all_records.extend(table_records)

            # Strategy 3: Counter/odometer widgets
            counter_records = self._extract_counter_elements(soup)
            all_records.extend(counter_records)

            # Strategy 4: Inline numbers with context
            inline_records = self._extract_inline_numbers(soup)
            all_records.extend(inline_records)

            # Discover PDF links for reference
            pdf_links = self._discover_pdf_links(soup, self.source_url)
            all_pdf_links.extend(pdf_links)

            page_total = (
                len(stat_records) + len(table_records)
                + len(counter_records) + len(inline_records)
            )
            logger.info(
                "[%s] Page %s: %d records, %d PDF links",
                self.name, page_url, page_total, len(pdf_links),
            )

        # Record discovered PDF links as metadata records
        seen_pdfs: set[str] = set()
        for pdf_url in all_pdf_links:
            if pdf_url in seen_pdfs:
                continue
            seen_pdfs.add(pdf_url)

            all_records.append({
                "source_name": self.name,
                "report_year": self._extract_year(pdf_url) or now.year,
                "report_title": "Roshni Helpline - Discovered Report Link",
                "indicator": "report_link_discovered",
                "value": 1,
                "unit": "link",
                "geographic_scope": "Pakistan",
                "extraction_method": "html_link_discovery",
                "extraction_confidence": 0.5,
                "pdf_url": pdf_url,
                "scraped_at": now.isoformat(),
            })

        logger.info(
            "[%s] Total records: %d (including %d PDF link records)",
            self.name, len(all_records), len(seen_pdfs),
        )
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Roshni Helpline statistical report record.

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
