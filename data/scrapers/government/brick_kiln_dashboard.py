"""Urban Unit Brick Kiln Dashboard scraper.

Attempts to extract data from the Punjab Urban Unit's brick kiln
monitoring dashboard. The dashboard tracks approximately 10,000 brick
kilns, 126,000 children working at kilns, and their school enrollment
status. Built as a JavaScript dashboard, this scraper probes for
underlying API endpoints that serve the visualized data.

Source: https://dashboards.urbanunit.gov.pk/brick_kilns/
Schedule: Quarterly (0 7 1 */3 *)
Priority: P2 — Government dashboard with kiln-level detail
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import logging
import re

from data.scrapers.base_api_scraper import BaseAPIScraper

logger = logging.getLogger(__name__)

BASE_URL: str = "https://dashboards.urbanunit.gov.pk/brick_kilns/"

# Common API endpoint patterns used by JavaScript dashboards
_API_CANDIDATES: list[str] = [
    "api/",
    "api/data",
    "api/data/",
    "api/kilns",
    "api/kilns/",
    "api/dashboard",
    "api/dashboard/",
    "api/statistics",
    "api/statistics/",
    "api/summary",
    "api/summary/",
    "data.json",
    "data/",
    "stats/",
    "stats.json",
    "ajax/data",
    "get_data",
    "get_data/",
]


class BrickKilnDashboardScraper(BaseAPIScraper):
    """Scraper for Urban Unit brick kiln monitoring dashboard.

    Probes common API endpoint patterns behind the JS dashboard to
    find the underlying JSON data. Falls back to extracting statistics
    from the dashboard HTML if no API is found.
    """

    name: str = "brick_kiln_dashboard"
    source_url: str = BASE_URL
    schedule: str = "0 7 1 */3 *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0
    request_timeout: float = 45.0

    async def scrape(self) -> list[dict[str, Any]]:
        """Probe for dashboard API endpoints and extract data."""
        records: list[dict[str, Any]] = []

        # Step 1: Fetch the dashboard page to find JS-referenced API URLs
        api_urls = await self._discover_api_endpoints()

        # Step 2: Try each discovered/candidate API endpoint
        for api_url in api_urls:
            try:
                data = await self._try_json_endpoint(api_url)
                if data is not None:
                    parsed = self._parse_api_response(data, api_url)
                    if parsed:
                        records.extend(parsed)
                        logger.info(
                            "[%s] Extracted %d records from %s",
                            self.name, len(parsed), api_url,
                        )
            except Exception as exc:
                logger.debug(
                    "[%s] API probe failed for %s: %s",
                    self.name, api_url, exc,
                )

        # Step 3: Fallback — extract stats from dashboard HTML
        if not records:
            logger.info("[%s] No API data found; falling back to HTML extraction", self.name)
            records = await self._extract_from_html()

        return records

    async def _discover_api_endpoints(self) -> list[str]:
        """Fetch the dashboard page and discover API URLs from JS/HTML."""
        urls: list[str] = []

        try:
            response = await self.fetch(BASE_URL)
            html = response.text

            # Find URLs in JavaScript source
            # Patterns: fetch("/api/data"), axios.get("/api/..."), $.ajax({url: "..."})
            js_url_pattern = re.compile(
                r"""(?:fetch|get|post|ajax|url)\s*\(\s*['"]([^'"]+)['"]""",
                re.IGNORECASE,
            )
            for match in js_url_pattern.finditer(html):
                candidate = match.group(1)
                if candidate.startswith("/") or candidate.startswith("http"):
                    full_url = (
                        candidate if candidate.startswith("http")
                        else urljoin(BASE_URL, candidate)
                    )
                    urls.append(full_url)

            # Find data-url or data-source attributes
            attr_pattern = re.compile(
                r'data-(?:url|source|api)\s*=\s*["\']([^"\']+)["\']',
                re.IGNORECASE,
            )
            for match in attr_pattern.finditer(html):
                urls.append(urljoin(BASE_URL, match.group(1)))

            # Find script src references that might be API proxies
            script_pattern = re.compile(
                r'<script[^>]+src\s*=\s*["\']([^"\']*api[^"\']*)["\']',
                re.IGNORECASE,
            )
            for match in script_pattern.finditer(html):
                urls.append(urljoin(BASE_URL, match.group(1)))

        except Exception as exc:
            logger.warning(
                "[%s] Failed to fetch dashboard page: %s", self.name, exc
            )

        # Add standard candidate URLs
        for candidate in _API_CANDIDATES:
            urls.append(urljoin(BASE_URL, candidate))

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique.append(url)

        logger.info("[%s] Discovered %d API candidate URLs", self.name, len(unique))
        return unique

    async def _try_json_endpoint(self, url: str) -> dict | list | None:
        """Attempt to fetch JSON from a URL, returning None on failure."""
        try:
            response = await self.fetch(
                url,
                headers={"Accept": "application/json"},
            )
            content_type = response.headers.get("content-type", "")
            if "json" in content_type or "javascript" in content_type:
                return response.json()

            # Try to parse as JSON even without proper content-type
            text = response.text.strip()
            if text.startswith(("{", "[")):
                import json
                return json.loads(text)

        except Exception:
            pass

        return None

    def _parse_api_response(
        self, data: dict | list, api_url: str
    ) -> list[dict[str, Any]]:
        """Parse a JSON API response into statistical_reports records."""
        records: list[dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        if isinstance(data, dict):
            records.extend(self._extract_from_dict(data, api_url, now_iso))
        elif isinstance(data, list):
            # Could be a list of kiln records or summary objects
            if data and isinstance(data[0], dict):
                summary = self._summarize_list(data)
                for key, value in summary.items():
                    records.append({
                        "source_name": self.name,
                        "report_year": str(datetime.now(timezone.utc).year),
                        "report_title": "Urban Unit Brick Kiln Dashboard",
                        "indicator": key,
                        "value": value,
                        "unit": "count",
                        "geographic_scope": "Punjab",
                        "pdf_url": None,
                        "extraction_method": "dashboard_api_json",
                        "extraction_confidence": 0.85,
                        "victim_gender": None,
                        "victim_age_bracket": None,
                        "api_url": api_url,
                        "scraped_at": now_iso,
                    })

        return records

    def _extract_from_dict(
        self, data: dict, api_url: str, now_iso: str
    ) -> list[dict[str, Any]]:
        """Extract records from a dictionary response."""
        records: list[dict[str, Any]] = []

        for key, value in data.items():
            key_lower = key.lower().replace("-", "_").replace(" ", "_")

            if isinstance(value, (int, float)):
                records.append({
                    "source_name": self.name,
                    "report_year": str(datetime.now(timezone.utc).year),
                    "report_title": "Urban Unit Brick Kiln Dashboard",
                    "indicator": key_lower,
                    "value": value,
                    "unit": "count",
                    "geographic_scope": "Punjab",
                    "pdf_url": None,
                    "extraction_method": "dashboard_api_json",
                    "extraction_confidence": 0.85,
                    "victim_gender": None,
                    "victim_age_bracket": None,
                    "api_url": api_url,
                    "scraped_at": now_iso,
                })
            elif isinstance(value, dict):
                # Nested object — flatten one level
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (int, float)):
                        indicator = f"{key_lower}_{sub_key.lower()}"
                        records.append({
                            "source_name": self.name,
                            "report_year": str(datetime.now(timezone.utc).year),
                            "report_title": "Urban Unit Brick Kiln Dashboard",
                            "indicator": indicator,
                            "value": sub_value,
                            "unit": "count",
                            "geographic_scope": "Punjab",
                            "pdf_url": None,
                            "extraction_method": "dashboard_api_json",
                            "extraction_confidence": 0.80,
                            "victim_gender": None,
                            "victim_age_bracket": None,
                            "api_url": api_url,
                            "scraped_at": now_iso,
                        })

        return records

    @staticmethod
    def _summarize_list(data: list[dict]) -> dict[str, int]:
        """Summarize a list of records into aggregate counts."""
        summary: dict[str, int] = {"total_records": len(data)}

        # Count unique districts
        districts: set[str] = set()
        children_total = 0

        for item in data:
            for key, value in item.items():
                key_lower = key.lower()
                if "district" in key_lower and value:
                    districts.add(str(value))
                if "children" in key_lower or "child" in key_lower:
                    try:
                        children_total += int(value)
                    except (ValueError, TypeError):
                        pass

        if districts:
            summary["unique_districts"] = len(districts)
        if children_total > 0:
            summary["total_children"] = children_total

        return summary

    async def _extract_from_html(self) -> list[dict[str, Any]]:
        """Fallback: extract statistics from dashboard HTML page."""
        records: list[dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            response = await self.fetch(BASE_URL)
            html = response.text
        except Exception as exc:
            logger.error("[%s] Failed to fetch dashboard HTML: %s", self.name, exc)
            return []

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        # Look for statistics displayed as counters or summary cards
        # Common patterns: "10,234 Kilns", "126,000 Children"
        stat_patterns = [
            (
                re.compile(r"([\d,]+)\s*\+?\s*(?:brick\s+)?kilns?", re.IGNORECASE),
                "total_kilns",
            ),
            (
                re.compile(r"([\d,]+)\s*\+?\s*children", re.IGNORECASE),
                "total_children",
            ),
            (
                re.compile(r"([\d,]+)\s*\+?\s*(?:enrolled|enrollment|school)", re.IGNORECASE),
                "school_enrollment",
            ),
            (
                re.compile(r"([\d,]+)\s*\+?\s*districts?", re.IGNORECASE),
                "total_districts",
            ),
            (
                re.compile(r"([\d,]+)\s*\+?\s*workers?", re.IGNORECASE),
                "total_workers",
            ),
        ]

        for pattern, indicator in stat_patterns:
            match = pattern.search(text)
            if match:
                value_str = match.group(1).replace(",", "")
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                records.append({
                    "source_name": self.name,
                    "report_year": str(datetime.now(timezone.utc).year),
                    "report_title": "Urban Unit Brick Kiln Dashboard",
                    "indicator": indicator,
                    "value": value,
                    "unit": "count",
                    "geographic_scope": "Punjab",
                    "pdf_url": None,
                    "extraction_method": "html_text_regex",
                    "extraction_confidence": 0.55,
                    "victim_gender": None,
                    "victim_age_bracket": None,
                    "scraped_at": now_iso,
                })

        # Also try to extract from counter/card elements
        for el in soup.find_all(class_=re.compile(r"counter|stat|card|number|count", re.I)):
            el_text = el.get_text(strip=True)
            num_match = re.search(r"[\d,]+", el_text)
            if num_match:
                value_str = num_match.group().replace(",", "")
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                # Infer indicator from surrounding text
                parent_text = ""
                if el.parent:
                    parent_text = el.parent.get_text(separator=" ", strip=True).lower()

                indicator = "dashboard_metric"
                if "kiln" in parent_text:
                    indicator = "total_kilns"
                elif "child" in parent_text:
                    indicator = "total_children"
                elif "enroll" in parent_text or "school" in parent_text:
                    indicator = "school_enrollment"
                elif "district" in parent_text:
                    indicator = "total_districts"

                records.append({
                    "source_name": self.name,
                    "report_year": str(datetime.now(timezone.utc).year),
                    "report_title": "Urban Unit Brick Kiln Dashboard",
                    "indicator": indicator,
                    "value": value,
                    "unit": "count",
                    "geographic_scope": "Punjab",
                    "pdf_url": None,
                    "extraction_method": "html_element_extraction",
                    "extraction_confidence": 0.50,
                    "victim_gender": None,
                    "victim_age_bracket": None,
                    "scraped_at": now_iso,
                })

        # Deduplicate
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for record in records:
            key = record.get("indicator", "")
            if key not in seen:
                seen.add(key)
                unique.append(record)

        return unique

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a brick kiln dashboard record."""
        if not record.get("source_name"):
            return False
        if not record.get("indicator"):
            return False
        if record.get("value") is None:
            return False
        return True
