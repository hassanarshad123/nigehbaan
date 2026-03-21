"""NCHR (National Commission for Human Rights) organ trafficking scraper.

Scrapes NCHR publications for reports on organ trafficking, human
rights violations, and related studies. The NCHR has published an
organ trafficking study and other reports relevant to child protection.

URL: https://nchr.gov.pk
Schedule: Annually (0 0 15 4 *)
Priority: P2
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse
import logging
import re

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Wayback Machine prefix for fallback
_WAYBACK_PREFIX = "https://web.archive.org/web/2024/"

# Keywords identifying organ trafficking and related reports
_ORGAN_KEYWORDS: list[str] = [
    "organ trafficking",
    "organ trade",
    "organ harvest",
    "kidney",
    "transplant",
    "illegal organ",
    "organ removal",
    "organ sale",
    "human trafficking",
    "child trafficking",
    "bonded lab",
    "forced lab",
    "human rights",
]

# Known NCHR sub-pages that may host reports
_REPORT_PAGES: list[str] = [
    "https://nchr.gov.pk/publications/",
    "https://nchr.gov.pk/reports/",
    "https://nchr.gov.pk/resources/",
    "https://nchr.gov.pk/research/",
    "https://nchr.gov.pk/annual-reports/",
    "https://nchr.gov.pk/special-reports/",
    "https://nchr.gov.pk/category/reports/",
    "https://nchr.gov.pk/category/publications/",
]


class NCHROrganScraper(BaseScraper):
    """Scraper for NCHR publications on organ trafficking and human rights.

    Scans the NCHR website (main page and sub-pages) for PDF
    publications, with particular focus on the organ trafficking
    study. Extracts metadata and produces statistical_reports records.

    URL: https://nchr.gov.pk
    Schedule: Annually
    Priority: P2
    """

    name: str = "nchr_organ"
    source_url: str = "https://nchr.gov.pk"
    schedule: str = "0 0 15 4 *"
    priority: str = "P2"
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
                "[%s] Live fetch failed for %s (%s), trying Wayback Machine",
                self.name, url, exc,
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

    def _discover_pdf_links(self, html: str, base_url: str) -> list[dict[str, str]]:
        """Parse an HTML page for PDF links.

        Args:
            html: Raw HTML content.
            base_url: Base URL for resolving relative links.

        Returns:
            List of dicts with keys: title, pdf_url, context.
        """
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []
        seen: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)

            # Gather surrounding context for relevance checks
            parent_text = ""
            if link.parent:
                parent_text = link.parent.get_text(strip=True)

            combined = f"{text} {parent_text} {href}".lower()

            # Must contain a PDF link
            if ".pdf" not in href.lower():
                continue

            # Build absolute URL
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                parsed = urlparse(base_url)
                full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
            else:
                full_url = urljoin(base_url, href)

            if full_url in seen:
                continue
            seen.add(full_url)

            title = text if text else href.split("/")[-1].replace(".pdf", "")
            results.append({
                "title": title.strip(),
                "pdf_url": full_url,
                "context": combined[:300],
            })

        return results

    def _is_relevant(self, text: str) -> bool:
        """Check if text relates to organ trafficking or human rights.

        Args:
            text: Combined title/context text.

        Returns:
            True if any relevant keyword is found.
        """
        text_lower = text.lower()
        return any(kw in text_lower for kw in _ORGAN_KEYWORDS)

    def _classify_indicator(self, text: str) -> str:
        """Classify the report topic into an indicator name.

        Args:
            text: Combined title and context text.

        Returns:
            Indicator string.
        """
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["organ trafficking", "organ trade", "organ harvest", "kidney", "transplant"]):
            return "organ_trafficking"
        if any(kw in text_lower for kw in ["human trafficking", "child trafficking"]):
            return "human_trafficking"
        if any(kw in text_lower for kw in ["bonded lab", "forced lab"]):
            return "forced_labor"
        if "human rights" in text_lower:
            return "human_rights_report"

        return "nchr_publication"

    def _extract_year(self, text: str) -> int | None:
        """Extract a 4-digit year from text.

        Args:
            text: Text to search for a year.

        Returns:
            Year as integer or None.
        """
        range_match = re.search(r"(20[0-2]\d)[-–](\d{2})", text)
        if range_match:
            return int(range_match.group(1))
        single_match = re.search(r"20[0-2]\d", text)
        if single_match:
            return int(single_match.group())
        return None

    async def _extract_report_stats(
        self, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Download a PDF and extract statistical data.

        Looks for numeric patterns related to organ trafficking
        and human rights cases.

        Args:
            pdf_url: URL of the PDF file.

        Returns:
            List of statistical_reports records from the PDF.
        """
        try:
            import pdfplumber
        except ImportError:
            logger.warning(
                "[%s] pdfplumber not installed, skipping PDF extraction",
                self.name,
            )
            return []

        raw_dir = self.get_raw_dir()
        filename = pdf_url.split("/")[-1].split("?")[0]
        if not filename.endswith(".pdf"):
            filename = f"nchr_{self.run_id}.pdf"
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
            logger.warning(
                "[%s] PDF text extraction failed for %s: %s",
                self.name, pdf_url, exc,
            )
            return []

        if not text:
            return []

        return self._parse_report_text(text, pdf_url)

    def _parse_report_text(
        self, text: str, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Extract organ trafficking / human rights stats from PDF text.

        Args:
            text: Extracted text from the PDF.
            pdf_url: Source URL for provenance.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        year = self._extract_year(pdf_url) or datetime.now(timezone.utc).year
        now = datetime.now(timezone.utc).isoformat()

        # Patterns for organ trafficking case numbers
        patterns = [
            (r"(\d{1,6})\s*(?:cases|incidents|victims)\s*(?:of\s+)?organ\s+trafficking", "organ_trafficking"),
            (r"organ\s+trafficking\s*[:\-]?\s*(\d{1,6})\s*(?:cases|incidents)?", "organ_trafficking"),
            (r"(\d{1,6})\s*(?:kidney|organ)\s*(?:removals|transplants|sales)", "organ_trafficking"),
            (r"(\d{1,6})\s*(?:cases|incidents|complaints)\s*(?:of\s+)?human\s+trafficking", "human_trafficking"),
            (r"(\d{1,6})\s*(?:cases|incidents)\s*(?:of\s+)?(?:bonded|forced)\s+lab", "forced_labor"),
        ]

        for pattern, indicator in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value_str = match.group(1)
                if value_str and value_str.isdigit():
                    records.append({
                        "source_name": self.name,
                        "report_year": year,
                        "report_title": f"NCHR Report {year}",
                        "indicator": indicator,
                        "value": int(value_str),
                        "unit": "cases",
                        "geographic_scope": "Pakistan",
                        "pdf_url": pdf_url,
                        "extraction_method": "pdf_text_regex",
                        "extraction_confidence": 0.55,
                        "scraped_at": now,
                    })

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch NCHR pages, discover PDFs, and extract data.

        Checks the main page and known sub-pages for PDF links.
        Filters for organ trafficking and human rights relevance.
        Gracefully continues if individual pages are unreachable.

        Returns:
            List of statistical_reports records.
        """
        all_pdf_links: list[dict[str, str]] = []

        # Fetch main page
        html = await self._fetch_page(self.source_url)
        if html:
            links = self._discover_pdf_links(html, self.source_url)
            all_pdf_links.extend(links)
            logger.info(
                "[%s] Found %d PDF links on main page",
                self.name, len(links),
            )
        else:
            logger.warning("[%s] Could not fetch main page", self.name)

        # Fetch known sub-pages
        for page_url in _REPORT_PAGES:
            page_html = await self._fetch_page(page_url)
            if page_html:
                links = self._discover_pdf_links(page_html, page_url)
                all_pdf_links.extend(links)
                logger.info(
                    "[%s] Found %d PDF links on %s",
                    self.name, len(links), page_url,
                )
            else:
                logger.warning(
                    "[%s] Could not fetch sub-page: %s", self.name, page_url,
                )

        # Deduplicate by URL
        seen: set[str] = set()
        unique_links: list[dict[str, str]] = []
        for link in all_pdf_links:
            if link["pdf_url"] not in seen:
                seen.add(link["pdf_url"])
                unique_links.append(link)

        if not unique_links:
            logger.warning("[%s] No PDF links found across all pages", self.name)
            return []

        logger.info(
            "[%s] Processing %d unique PDF links",
            self.name, len(unique_links),
        )

        now = datetime.now(timezone.utc).isoformat()
        all_records: list[dict[str, Any]] = []

        for link in unique_links:
            pdf_url = link["pdf_url"]
            title = link["title"]
            context = link.get("context", "")
            year = self._extract_year(f"{title} {pdf_url}")

            is_relevant = self._is_relevant(f"{title} {context}")
            indicator = self._classify_indicator(f"{title} {context}")

            # Create a metadata record for every PDF found
            base_record = {
                "source_name": self.name,
                "report_year": year or datetime.now(timezone.utc).year,
                "report_title": title,
                "indicator": indicator,
                "value": None,
                "unit": "report",
                "geographic_scope": "Pakistan",
                "pdf_url": pdf_url,
                "extraction_method": "pdf_link",
                "extraction_confidence": 0.60 if is_relevant else 0.40,
                "scraped_at": now,
            }

            # For relevant PDFs, try deeper extraction
            if is_relevant:
                try:
                    pdf_records = await self._extract_report_stats(pdf_url)
                    if pdf_records:
                        all_records.extend(pdf_records)
                        continue  # Skip the base record
                except Exception as exc:
                    logger.warning(
                        "[%s] PDF extraction failed for %s: %s",
                        self.name, pdf_url, exc,
                    )

            all_records.append(base_record)

        logger.info("[%s] Total records: %d", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an NCHR organ trafficking record.

        Requires source_name and either indicator or report_title.

        Args:
            record: Dictionary representing one scraped record.

        Returns:
            True if the record passes validation.
        """
        return bool(
            record.get("source_name")
            and (record.get("indicator") or record.get("report_title"))
        )
