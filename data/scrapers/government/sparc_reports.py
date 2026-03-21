"""SPARC (Society for the Protection of the Rights of the Child) scraper.

Scrapes SPARC's website for their annual "State of Pakistan's Children"
reports and other child rights publications. SPARC is a leading
Pakistani NGO producing comprehensive annual data on child welfare.

URL: https://sparcpk.org/
Schedule: Annually (0 0 1 3 *)
Priority: P1
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

# Keywords for identifying SPARC child rights publications
_SPARC_KEYWORDS: list[str] = [
    "state of children",
    "state of pakistan",
    "annual report",
    "child rights",
    "child protection",
    "child labour",
    "child labor",
    "child marriage",
    "child health",
    "child education",
    "juvenile justice",
    "child trafficking",
    "child abuse",
    "birth registration",
    "street children",
    "child poverty",
    "out of school",
    "violence against children",
]

# SPARC known sub-pages likely to contain publications
_PUBLICATION_PAGES: list[str] = [
    "https://sparcpk.org/publications/",
    "https://sparcpk.org/resources/",
    "https://sparcpk.org/reports/",
    "https://sparcpk.org/state-of-pakistans-children/",
    "https://sparcpk.org/category/publications/",
    "https://sparcpk.org/category/reports/",
    "https://sparcpk.org/annual-reports/",
    "https://sparcpk.org/research/",
]

# SPARC report indicators
_INDICATOR_MAP: dict[str, list[str]] = {
    "child_labor": ["child lab", "child work", "working child", "bonded lab"],
    "child_marriage": ["child marriage", "early marriage", "underage marriage"],
    "child_education": ["education", "school", "enrolment", "out of school", "dropout"],
    "child_health": ["health", "nutrition", "stunting", "wasting", "mortality", "immunization"],
    "child_protection": ["child protection", "violence", "abuse", "exploitation"],
    "juvenile_justice": ["juvenile justice", "juvenile", "jjsa", "diversion"],
    "child_trafficking": ["trafficking", "traffick", "smuggling"],
    "birth_registration": ["birth registr", "nadra", "registered"],
    "street_children": ["street child", "homeless child"],
    "child_poverty": ["poverty", "deprivation", "mpi"],
}


class SPARCReportsScraper(BaseScraper):
    """Scraper for SPARC child rights publications.

    SPARC publishes annual "State of Pakistan's Children" reports
    with comprehensive statistics on child welfare, protection,
    education, health, and justice. This scraper discovers and
    processes those publications.

    URL: https://sparcpk.org/
    Schedule: Annually
    Priority: P1
    """

    name: str = "sparc_reports"
    source_url: str = "https://sparcpk.org/"
    schedule: str = "0 0 1 3 *"
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

    def _discover_publications(
        self, html: str, base_url: str
    ) -> list[dict[str, str]]:
        """Parse an HTML page for SPARC publication and PDF links.

        Finds both direct PDF links and publication page links
        containing child-rights-related keywords.

        Args:
            html: Raw HTML content.
            base_url: Base URL for resolving relative links.

        Returns:
            List of dicts with keys: title, url, is_pdf.
        """
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []
        seen: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)

            # Gather surrounding context
            parent_text = ""
            if link.parent:
                parent_text = link.parent.get_text(strip=True)

            combined = f"{text} {parent_text} {href}".lower()

            is_pdf = ".pdf" in href.lower()

            # Check relevance: must match SPARC keywords or be a PDF
            is_relevant = any(kw in combined for kw in _SPARC_KEYWORDS)

            if not (is_pdf or is_relevant):
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
                "url": full_url,
                "is_pdf": str(is_pdf),
            })

        return results

    def _extract_year(self, text: str) -> int | None:
        """Extract a 4-digit year from text or URL.

        Args:
            text: Text to search.

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

    def _classify_indicator(self, text: str) -> str:
        """Classify text into a SPARC indicator category.

        Args:
            text: Combined title and context text.

        Returns:
            Standardized indicator name.
        """
        text_lower = text.lower()
        for indicator, keywords in _INDICATOR_MAP.items():
            if any(kw in text_lower for kw in keywords):
                return indicator
        return "child_rights_report"

    async def _extract_pdf_data(
        self, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Download a PDF and extract child welfare statistics.

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
            filename = f"sparc_{self.run_id}.pdf"
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
        """Extract statistics from SPARC report text.

        Looks for numeric patterns related to child welfare indicators
        such as child labor, marriage, education, health, etc.

        Args:
            text: Extracted text from the PDF.
            pdf_url: Source URL for provenance.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        year = self._extract_year(pdf_url) or datetime.now(timezone.utc).year
        now = datetime.now(timezone.utc).isoformat()

        # Pattern: "X.X million children" or "X,XXX children"
        count_patterns = [
            (
                r"(\d+(?:\.\d+)?)\s*million\s*children",
                lambda m: int(float(m.group(1)) * 1_000_000),
                "count",
            ),
            (
                r"(\d{1,3}(?:,\d{3})+)\s*children",
                lambda m: int(m.group(1).replace(",", "")),
                "count",
            ),
            (
                r"(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?children",
                lambda m: float(m.group(1)),
                "percent",
            ),
        ]

        for pattern, value_fn, unit in count_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = max(0, match.start() - 200)
                context = text[start:match.end() + 100].strip()

                indicator = self._classify_indicator(context)

                try:
                    value = value_fn(match)
                except (ValueError, IndexError):
                    continue

                # Detect province if mentioned nearby
                province = self._detect_province(context)

                records.append({
                    "source_name": self.name,
                    "report_year": year,
                    "report_title": f"State of Pakistan's Children {year}",
                    "indicator": indicator,
                    "value": value,
                    "unit": unit,
                    "geographic_scope": province or "Pakistan",
                    "pdf_url": pdf_url,
                    "extraction_method": "pdf_text_regex",
                    "extraction_confidence": 0.50,
                    "victim_age_bracket": "0-18",
                    "scraped_at": now,
                })

        return records

    @staticmethod
    def _detect_province(text: str) -> str | None:
        """Detect a Pakistan province name in text.

        Args:
            text: Text to search.

        Returns:
            Province name or None.
        """
        provinces = [
            "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan",
            "Islamabad Capital Territory",
        ]
        text_lower = text.lower()
        for province in provinces:
            if province.lower() in text_lower:
                return province

        abbreviations = {
            "kp": "Khyber Pakhtunkhwa",
            "kpk": "Khyber Pakhtunkhwa",
            "ict": "Islamabad Capital Territory",
        }
        for abbrev, full_name in abbreviations.items():
            if re.search(rf"\b{abbrev}\b", text_lower):
                return full_name

        return None

    async def _scan_publication_page(
        self, page_url: str
    ) -> list[dict[str, str]]:
        """Fetch and scan a single publication page for links.

        Args:
            page_url: URL of the page to scan.

        Returns:
            List of discovered publication link dicts.
        """
        html = await self._fetch_page(page_url)
        if not html:
            return []
        return self._discover_publications(html, page_url)

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch SPARC pages, discover publications, and extract data.

        Checks the main site and known publication sub-pages.
        Prioritizes "State of Pakistan's Children" annual reports.
        Gracefully continues if individual pages are unreachable.

        Returns:
            List of statistical_reports records.
        """
        all_pub_links: list[dict[str, str]] = []

        # Fetch main page
        main_html = await self._fetch_page(self.source_url)
        if main_html:
            links = self._discover_publications(main_html, self.source_url)
            all_pub_links.extend(links)
            logger.info(
                "[%s] Found %d links on main page", self.name, len(links),
            )
        else:
            logger.warning("[%s] Could not fetch main page", self.name)

        # Fetch known publication sub-pages
        for page_url in _PUBLICATION_PAGES:
            try:
                links = await self._scan_publication_page(page_url)
                all_pub_links.extend(links)
                if links:
                    logger.info(
                        "[%s] Found %d links on %s",
                        self.name, len(links), page_url,
                    )
            except Exception as exc:
                logger.warning(
                    "[%s] Failed to scan %s: %s",
                    self.name, page_url, exc,
                )

        # Deduplicate by URL
        seen: set[str] = set()
        unique_links: list[dict[str, str]] = []
        for link in all_pub_links:
            if link["url"] not in seen:
                seen.add(link["url"])
                unique_links.append(link)

        if not unique_links:
            logger.warning(
                "[%s] No publication links found across all pages",
                self.name,
            )
            return []

        logger.info(
            "[%s] Processing %d unique publication links",
            self.name, len(unique_links),
        )

        now = datetime.now(timezone.utc).isoformat()
        all_records: list[dict[str, Any]] = []

        for link in unique_links:
            pub_url = link["url"]
            title = link["title"]
            is_pdf = link.get("is_pdf") == "True"
            year = self._extract_year(f"{title} {pub_url}")
            indicator = self._classify_indicator(title)

            # Determine if this is a "State of Children" report
            is_soc = any(
                kw in title.lower()
                for kw in ["state of children", "state of pakistan", "annual report"]
            )
            report_title = (
                f"State of Pakistan's Children {year or ''}"
                if is_soc
                else title
            ).strip()

            base_record = {
                "source_name": self.name,
                "report_year": year or datetime.now(timezone.utc).year,
                "report_title": report_title,
                "indicator": indicator,
                "value": None,
                "unit": "report",
                "geographic_scope": "Pakistan",
                "pdf_url": pub_url if is_pdf else None,
                "page_url": pub_url if not is_pdf else None,
                "extraction_method": "pdf_link",
                "extraction_confidence": 0.60,
                "scraped_at": now,
            }

            # For PDFs, attempt deeper extraction
            if is_pdf:
                try:
                    pdf_records = await self._extract_pdf_data(pub_url)
                    if pdf_records:
                        all_records.extend(pdf_records)
                        continue  # Skip the base record
                except Exception as exc:
                    logger.warning(
                        "[%s] PDF extraction failed for %s: %s",
                        self.name, pub_url, exc,
                    )

            all_records.append(base_record)

        logger.info("[%s] Total records: %d", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a SPARC reports record.

        Requires source_name and report_title.

        Args:
            record: Dictionary representing one scraped record.

        Returns:
            True if the record passes validation.
        """
        return bool(
            record.get("source_name")
            and record.get("report_title")
        )
