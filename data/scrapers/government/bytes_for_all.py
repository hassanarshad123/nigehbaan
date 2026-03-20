"""Bytes for All Pakistan — Internet Landscape Report scraper.

Scrapes Bytes for All (B4A) publications page for Internet Landscape
Reports and other publications documenting online rights, digital
safety, and child protection in Pakistan.

URL: https://bytesforall.pk/publications
Schedule: Annually (0 3 1 6 *)
Priority: P2
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urljoin
import re

import logging

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

_YEAR_PATTERN = re.compile(r"20[12]\d")
_NUMBER_PATTERN = re.compile(r"([\d,]+(?:\.\d+)?)")

# Keywords that indicate a publication is relevant to child protection
_RELEVANCE_KEYWORDS: list[str] = [
    "child",
    "minor",
    "internet landscape",
    "digital rights",
    "online safety",
    "cyber",
    "PECA",
    "harassment",
    "exploitation",
    "content regulation",
    "surveillance",
    "censorship",
    "blocking",
    "filtering",
    "gender",
    "women",
    "violence",
    "protection",
    "internet freedom",
    "digital literacy",
]

# Key metrics to extract from Internet Landscape Reports
_ILR_METRICS: dict[str, list[str]] = {
    "Internet Penetration Rate": [
        r"internet\s+penetration.*?(\d[\d,.]+)\s*%",
        r"(\d[\d,.]+)\s*%\s*(?:internet\s+)?penetration",
    ],
    "Total Internet Users": [
        r"(\d[\d,.]+)\s*(?:million\s+)?(?:internet\s+)?users",
        r"internet\s+users.*?(\d[\d,.]+)\s*million",
    ],
    "Mobile Internet Users": [
        r"(\d[\d,.]+)\s*(?:million\s+)?mobile\s+(?:internet\s+)?users",
        r"mobile.*?(\d[\d,.]+)\s*(?:million\s+)?users",
    ],
    "Social Media Users": [
        r"(\d[\d,.]+)\s*(?:million\s+)?social\s+media\s+users",
        r"social\s+media.*?(\d[\d,.]+)\s*million",
    ],
    "URLs Blocked": [
        r"(\d[\d,]+)\s*(?:URLs?|websites?)\s*(?:blocked|banned|filtered)",
        r"(?:blocked|banned|filtered).*?(\d[\d,]+)\s*(?:URLs?|websites?)",
    ],
    "PECA Cases Filed": [
        r"(\d[\d,]+)\s*(?:PECA\s+)?cases?\s*(?:filed|registered|reported)",
        r"PECA.*?(\d[\d,]+)\s*cases?",
    ],
    "Content Removal Requests": [
        r"(\d[\d,]+)\s*(?:content\s+)?removal\s*requests?",
        r"removal\s*requests?.*?(\d[\d,]+)",
    ],
    "Cyber Crime Complaints": [
        r"(\d[\d,]+)\s*(?:cyber\s*)?(?:crime\s+)?complaints?",
        r"complaints?.*?(\d[\d,]+)",
    ],
    "Online Harassment Reports": [
        r"(\d[\d,]+)\s*(?:online\s+)?harassment\s*(?:reports?|complaints?|cases?)",
    ],
    "Child-Related Complaints": [
        r"(\d[\d,]+)\s*child.*?(?:complaints?|cases?|reports?)",
        r"child.*?(\d[\d,]+)\s*(?:complaints?|cases?|reports?)",
    ],
}


class BytesForAllScraper(BasePDFReportScraper):
    """Scraper for Bytes for All Pakistan publications.

    Discovers and downloads publications from the B4A website,
    focusing on Internet Landscape Reports and digital rights
    publications that contain data relevant to child online safety.
    """

    name: str = "bytes_for_all"
    source_url: str = "https://bytesforall.pk/publications"
    catalog_url: str = "https://bytesforall.pk/publications"
    schedule: str = "0 3 1 6 *"
    priority: str = "P2"
    rate_limit_delay: float = 2.0
    pdf_link_pattern: str = r"\.pdf"

    def _extract_year(self, text: str) -> int | None:
        """Extract a report year from text."""
        match = _YEAR_PATTERN.search(text)
        return int(match.group()) if match else None

    def _parse_numeric(self, text: str) -> float | None:
        """Parse a numeric value, handling commas and magnitude words."""
        cleaned = text.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return None
        if cleaned.endswith("%"):
            try:
                return float(cleaned[:-1])
            except ValueError:
                return None
        # Handle magnitude words in context
        magnitude_map = {
            "million": 1_000_000,
            "billion": 1_000_000_000,
            "thousand": 1_000,
        }
        text_lower = text.lower()
        for word, multiplier in magnitude_map.items():
            if word in text_lower:
                nums = _NUMBER_PATTERN.findall(text)
                if nums:
                    try:
                        return float(nums[0].replace(",", "")) * multiplier
                    except ValueError:
                        pass
        try:
            return float(cleaned) if "." in cleaned else float(int(cleaned))
        except ValueError:
            return None

    def _is_relevant_publication(self, title: str) -> bool:
        """Check if a publication title is relevant to our scope."""
        title_lower = title.lower()
        return any(kw in title_lower for kw in _RELEVANCE_KEYWORDS)

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from a PDF URL."""
        filename = url.split("/")[-1].split("?")[0]
        name = filename.replace(".pdf", "").replace("-", " ").replace("_", " ")
        return name.title()

    def discover_pdf_urls(self, html: str) -> list[str]:
        """Find publication PDF links, filtering for relevance.

        Overrides base to additionally check link text for relevance.

        Args:
            html: Raw HTML from the publications page.

        Returns:
            List of relevant PDF URLs.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)

            # Check if it's a PDF or looks like a publication link
            is_pdf = href.lower().endswith(".pdf")
            is_pub_link = any(
                kw in href.lower()
                for kw in ["publication", "report", "download", "document"]
            )

            if not (is_pdf or is_pub_link):
                continue

            # Check relevance from link text or URL
            combined_text = f"{text} {href}"
            if not self._is_relevant_publication(combined_text):
                # Still include PDFs even without keyword match
                # since they may contain relevant data
                if not is_pdf:
                    continue

            # Build absolute URL
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                parsed = urlparse(self.source_url)
                full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
            else:
                full_url = urljoin(self.source_url, href)

            if full_url not in seen:
                seen.add(full_url)
                urls.append(full_url)

        return urls

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Convert B4A PDF tables into statistical_reports records.

        Args:
            tables: Raw tables from PDF extraction.
            pdf_url: Source URL for provenance.

        Returns:
            List of normalized statistical_reports records.
        """
        report_year = self._extract_year(pdf_url)
        title = self._extract_title_from_url(pdf_url)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        for table in tables:
            if len(table) < 2:
                continue

            headers = table[0]
            # Look for year columns
            year_cols: dict[int, int] = {}
            for i, header in enumerate(headers):
                year_match = _YEAR_PATTERN.search(header)
                if year_match:
                    year_cols[i] = int(year_match.group())

            for row in table[1:]:
                indicator = row[0].strip() if row and row[0] else ""
                if not indicator:
                    continue

                if year_cols:
                    for col_idx, year in year_cols.items():
                        if col_idx < len(row):
                            value = self._parse_numeric(row[col_idx])
                            if value is not None:
                                unit = "percent" if "%" in row[col_idx] else "count"
                                records.append({
                                    "source_name": "Bytes for All Pakistan",
                                    "report_year": year,
                                    "report_title": title,
                                    "indicator": indicator,
                                    "value": value,
                                    "unit": unit,
                                    "geographic_scope": "Pakistan",
                                    "pdf_url": pdf_url,
                                    "extraction_method": "pdfplumber_table",
                                    "scraped_at": now,
                                })
                else:
                    # No year columns — take second cell as value
                    if len(row) >= 2:
                        value = self._parse_numeric(row[1])
                        if value is not None:
                            unit = "percent" if "%" in row[1] else "count"
                            records.append({
                                "source_name": "Bytes for All Pakistan",
                                "report_year": report_year,
                                "report_title": title,
                                "indicator": indicator,
                                "value": value,
                                "unit": unit,
                                "geographic_scope": "Pakistan",
                                "pdf_url": pdf_url,
                                "extraction_method": "pdfplumber_table",
                                "scraped_at": now,
                            })

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the B4A publications scraping pipeline.

        Fetches the publications page, discovers relevant PDFs,
        downloads them, and extracts statistics from tables and text.
        """
        url = self.catalog_url
        response = await self.fetch(url)
        pdf_urls = self.discover_pdf_urls(response.text)

        if not pdf_urls:
            logger.warning("[%s] No relevant PDF URLs found at %s", self.name, url)
            return []

        logger.info("[%s] Discovered %d relevant publication URLs", self.name, len(pdf_urls))

        all_records: list[dict[str, Any]] = []
        for pdf_url in pdf_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)

                # Try table extraction
                tables = self.extract_tables(pdf_path)
                table_records = self.parse_tables(tables, pdf_url)

                if table_records:
                    all_records.extend(table_records)

                # Also extract from text for key metrics
                text_records = self._extract_from_text(pdf_path, pdf_url)
                existing = {r["indicator"] for r in table_records}
                for tr in text_records:
                    if tr["indicator"] not in existing:
                        all_records.append(tr)
            except Exception as exc:
                logger.error(
                    "[%s] Failed to process %s: %s", self.name, pdf_url, exc
                )

        return all_records

    def _extract_from_text(
        self, pdf_path: Path, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Extract key metrics from PDF text using regex patterns."""
        text = self.extract_text(pdf_path)
        if not text:
            return []

        report_year = self._extract_year(pdf_url) or self._extract_year(text)
        title = self._extract_title_from_url(pdf_url)
        now = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        for indicator_name, patterns in _ILR_METRICS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    raw_value = match.group(1)
                    # Check for magnitude words in surrounding text
                    context_start = max(0, match.start() - 20)
                    context_end = min(len(text), match.end() + 30)
                    context = text[context_start:context_end]

                    value = self._parse_numeric(context) or self._parse_numeric(raw_value)
                    if value is not None:
                        unit = "percent" if "%" in context else "count"
                        records.append({
                            "source_name": "Bytes for All Pakistan",
                            "report_year": report_year,
                            "report_title": title,
                            "indicator": indicator_name,
                            "value": value,
                            "unit": unit,
                            "geographic_scope": "Pakistan",
                            "pdf_url": pdf_url,
                            "extraction_method": "text_regex",
                            "scraped_at": now,
                        })
                        break

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a statistical_reports record from B4A.

        Requires source_name and indicator at minimum.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
            and (record.get("value") is not None or record.get("report_title"))
        )
