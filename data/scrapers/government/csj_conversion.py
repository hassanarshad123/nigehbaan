"""Centre for Social Justice Pakistan forced conversion publications scraper.

Scrapes the CSJ publication page for reports and PDFs documenting
forced conversion cases in Pakistan (515+ documented cases). Extracts
metadata (title, year, pdf_url) and produces statistical_reports records.

URL: https://csjpak.org/publication.php
Schedule: Annually (0 0 1 2 *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin
import logging
import re

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Wayback Machine prefix for fallback
_WAYBACK_PREFIX = "https://web.archive.org/web/2024/"

# Keywords that identify forced conversion publications
_CONVERSION_KEYWORDS: list[str] = [
    "forced conversion",
    "conversion",
    "minority",
    "hindu",
    "christian",
    "religious freedom",
    "kidnap",
    "abduct",
    "underage marriage",
    "child marriage",
    "forced marriage",
    "minority rights",
    "blasphemy",
]


class CSJConversionScraper(BaseScraper):
    """Scraper for Centre for Social Justice Pakistan publications.

    Targets publications documenting forced conversion cases across
    Pakistan (515+ cases). Discovers PDF links from the publications
    page, extracts metadata, and outputs statistical_reports records.

    URL: https://csjpak.org/publication.php
    Schedule: Annually
    Priority: P1
    """

    name: str = "csj_conversion"
    source_url: str = "https://csjpak.org/publication.php"
    schedule: str = "0 0 1 2 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    async def _fetch_page(self, url: str) -> str | None:
        """Fetch a page with Wayback Machine fallback.

        Args:
            url: Primary URL to fetch.

        Returns:
            HTML content or None if both live and archive fail.
        """
        try:
            response = await self.fetch(url)
            return response.text
        except Exception as exc:
            logger.warning(
                "[%s] Live site failed (%s), trying Wayback Machine",
                self.name, exc,
            )

        try:
            archive_url = f"{_WAYBACK_PREFIX}{url}"
            response = await self.fetch(archive_url)
            return response.text
        except Exception as exc:
            logger.error(
                "[%s] Wayback Machine also failed for %s: %s",
                self.name, url, exc,
            )
            return None

    def _extract_publications(self, html: str) -> list[dict[str, Any]]:
        """Parse the publications page for PDF links and metadata.

        Args:
            html: Raw HTML of the publications page.

        Returns:
            List of dicts with keys: title, year, pdf_url.
        """
        soup = BeautifulSoup(html, "html.parser")
        publications: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        # Look for links to PDFs
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            parent_text = ""
            if link.parent:
                parent_text = link.parent.get_text(strip=True)

            combined_text = f"{text} {parent_text}".lower()

            # Check if link points to a PDF
            is_pdf = ".pdf" in href.lower()

            # Check if the text or context is related to forced conversions
            is_relevant = any(
                kw in combined_text for kw in _CONVERSION_KEYWORDS
            )

            if not (is_pdf or is_relevant):
                continue

            # Build absolute URL
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = urljoin(self.source_url, href)
            else:
                base = self.source_url.rsplit("/", 1)[0]
                full_url = f"{base}/{href}"

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Extract year from text or URL
            year = self._extract_year(f"{text} {href}")

            title = text if text else href.split("/")[-1].replace(".pdf", "")

            publications.append({
                "title": title.strip(),
                "year": year,
                "pdf_url": full_url,
                "is_pdf": is_pdf,
            })

        return publications

    def _extract_year(self, text: str) -> int | None:
        """Extract a 4-digit year from text.

        Args:
            text: Text to search for a year.

        Returns:
            Year as integer or None.
        """
        # Try year ranges first (e.g., 2022-23)
        range_match = re.search(r"(20[0-2]\d)[-–](\d{2})", text)
        if range_match:
            return int(range_match.group(1))
        single_match = re.search(r"20[0-2]\d", text)
        if single_match:
            return int(single_match.group())
        return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch CSJ publications page and extract forced conversion data.

        Returns:
            List of statistical_reports records.
        """
        html = await self._fetch_page(self.source_url)
        if not html:
            logger.error("[%s] Could not fetch publications page", self.name)
            return []

        publications = self._extract_publications(html)

        if not publications:
            logger.warning(
                "[%s] No relevant publications found at %s",
                self.name, self.source_url,
            )
            return []

        logger.info(
            "[%s] Found %d publications on CSJ page",
            self.name, len(publications),
        )

        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        for pub in publications:
            year = pub["year"] or datetime.now(timezone.utc).year
            title = pub["title"]
            pdf_url = pub["pdf_url"]

            record = {
                "source_name": self.name,
                "report_year": year,
                "report_title": title,
                "indicator": "forced_conversion_cases",
                "value": None,
                "unit": "cases",
                "geographic_scope": "Pakistan",
                "pdf_url": pdf_url,
                "extraction_method": "pdf_link",
                "extraction_confidence": 0.60,
                "scraped_at": now,
            }

            # If it's a PDF, attempt to download and extract a case count
            if pub["is_pdf"]:
                try:
                    value = await self._extract_case_count(pdf_url)
                    if value is not None:
                        record["value"] = value
                        record["extraction_confidence"] = 0.75
                except Exception as exc:
                    logger.warning(
                        "[%s] Could not extract data from PDF %s: %s",
                        self.name, pdf_url, exc,
                    )

            records.append(record)

        logger.info("[%s] Produced %d records", self.name, len(records))
        return records

    async def _extract_case_count(self, pdf_url: str) -> int | None:
        """Try to extract a forced conversion case count from a PDF.

        Downloads the PDF, extracts text, and looks for numeric
        patterns associated with case counts.

        Args:
            pdf_url: URL of the PDF to process.

        Returns:
            Integer case count or None.
        """
        try:
            import pdfplumber
        except ImportError:
            logger.warning("[%s] pdfplumber not installed, skipping PDF text extraction", self.name)
            return None

        raw_dir = self.get_raw_dir()
        filename = pdf_url.split("/")[-1].split("?")[0]
        if not filename.endswith(".pdf"):
            filename = f"csj_{self.run_id}.pdf"
        file_path = raw_dir / filename

        content = await self.fetch_bytes(pdf_url)
        file_path.write_bytes(content)

        text = ""
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as exc:
            logger.warning("[%s] PDF text extraction failed: %s", self.name, exc)
            return None

        if not text:
            return None

        # Look for patterns like "515 cases", "total cases: 515"
        patterns = [
            r"(\d{2,5})\s*(?:cases|incidents)\s*(?:of\s+)?(?:forced\s+)?conversion",
            r"(?:total|documented|reported)\s*(?:cases|incidents)\s*[:\-]?\s*(\d{2,5})",
            r"conversion\s*cases\s*[:\-]?\s*(\d{2,5})",
            r"(\d{3,5})\s*(?:documented|reported|recorded)\s*cases",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                for group in groups:
                    if group and group.isdigit():
                        return int(group)

        return None

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a CSJ conversion statistical report record.

        Requires source_name, indicator, and report_title.

        Args:
            record: Dictionary representing one scraped record.

        Returns:
            True if the record passes validation.
        """
        return bool(
            record.get("source_name")
            and record.get("indicator")
            and record.get("report_title")
        )
