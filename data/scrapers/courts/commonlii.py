"""CommonLII (Commonwealth Legal Information Institute) scraper.

Scrapes CommonLII's free legal database for Pakistani court
decisions. CommonLII aggregates legal materials from Commonwealth
jurisdictions and provides bulk access to judgments.

Strategy:
    1. Access the Pakistan resources page on CommonLII
    2. Navigate to court-specific judgment listings
    3. Crawl available judgment pages
    4. Parse HTML judgment pages for structured data
    5. Filter for trafficking-related PPC sections

URL: https://www.commonlii.org/resources/245.html
Tool: Requests + BeautifulSoup for crawling (many pages)
Schedule: Monthly (0 3 1 * *)
Priority: P2 — Supplementary source for historical judgments
"""

import re
from typing import Any
from urllib.parse import urljoin

import logging

from bs4 import BeautifulSoup

from data.scrapers.courts.base_court_scraper import (
    BaseCourtScraper,
    extract_ppc_sections,
    filter_relevant_sections,
    parse_pakistani_date,
)

logger = logging.getLogger(__name__)

# Base URL for CommonLII Pakistan resources
COMMONLII_BASE = "https://www.commonlii.org"
PAKISTAN_INDEX_URL = "https://www.commonlii.org/resources/245.html"

# Patterns to identify judgment page URLs on CommonLII
JUDGMENT_URL_PATTERN = re.compile(
    r"/pk/(cases|legis|other|journals)/\w+/\d{4}/\d+\.html", re.IGNORECASE
)

# Pattern to extract year from CommonLII judgment URLs
YEAR_FROM_URL = re.compile(r"/(\d{4})/")

# Court name mapping from CommonLII path segments
COURT_PATH_MAP: dict[str, str] = {
    "PKSC": "Supreme Court of Pakistan",
    "PKLHC": "Lahore High Court",
    "PKSHC": "Sindh High Court",
    "PKPHC": "Peshawar High Court",
    "PKBHC": "Balochistan High Court",
    "PKIHC": "Islamabad High Court",
    "PKFSC": "Federal Shariat Court",
}


class CommonLIIScraper(BaseCourtScraper):
    """Scraper for CommonLII Pakistani court decisions.

    CommonLII provides a large archive of Pakistani court
    decisions in HTML format. This scraper crawls judgment pages
    using Requests + BeautifulSoup for efficient retrieval.

    CommonLII is particularly valuable for historical judgments
    that may not be available on individual court portals.

    Attributes:
        name: Scraper identifier.
        court_name: Multiple courts (aggregator).
        source_url: CommonLII Pakistan resources page.
        schedule: Monthly crawl.
    """

    name: str = "commonlii"
    court_name: str = "CommonLII (Multiple Courts)"
    source_url: str = "https://www.commonlii.org/resources/245.html"
    schedule: str = "0 3 1 * *"
    priority: str = "P2"
    rate_limit_delay: float = 3.0  # Be polite to CommonLII

    def __init__(self) -> None:
        super().__init__()
        self._discovered_urls: list[str] = []

    def _resolve_court_name(self, url: str) -> str:
        """Determine the court name from a CommonLII judgment URL.

        Args:
            url: CommonLII judgment URL.

        Returns:
            Human-readable court name.
        """
        for path_segment, court_name in COURT_PATH_MAP.items():
            if path_segment.lower() in url.lower():
                return court_name
        return "Unknown Pakistani Court"

    def _extract_year_from_url(self, url: str) -> str:
        """Extract the year from a CommonLII judgment URL path.

        Args:
            url: CommonLII judgment URL.

        Returns:
            Year string (e.g. '2023') or empty string.
        """
        match = YEAR_FROM_URL.search(url)
        return match.group(1) if match else ""

    async def _crawl_index_page(self, url: str) -> list[str]:
        """Crawl an index page and extract links.

        Args:
            url: URL of the index page to crawl.

        Returns:
            List of absolute URLs found on the page.
        """
        try:
            response = await self.fetch(url, method="GET")
            soup = BeautifulSoup(response.text, "html.parser")

            urls: list[str] = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute_url = urljoin(url, href)
                urls.append(absolute_url)

            return urls
        except Exception as exc:
            logger.warning("[%s] Failed to crawl index page %s: %s", self.name, url, exc)
            return []

    async def discover_judgment_urls(self) -> list[str]:
        """Discover all Pakistani judgment URLs from CommonLII index.

        Crawls the CommonLII Pakistan resources page and follows
        links to court-specific listing pages to build a complete
        index of available judgments.

        Returns:
            List of URLs pointing to individual judgment pages.
        """
        if self._discovered_urls:
            return self._discovered_urls

        logger.info("[%s] Discovering judgment URLs from %s", self.name, PAKISTAN_INDEX_URL)

        judgment_urls: list[str] = []
        visited: set[str] = set()

        # Step 1: Crawl the main Pakistan resources page
        top_level_links = await self._crawl_index_page(PAKISTAN_INDEX_URL)

        # Step 2: Identify court-specific index pages and judgment links
        court_index_pages: list[str] = []
        for link in top_level_links:
            if link in visited:
                continue
            visited.add(link)

            # Direct judgment links
            if JUDGMENT_URL_PATTERN.search(link):
                judgment_urls.append(link)
                continue

            # Court database index pages (e.g. /pk/cases/PKSC/)
            if "/pk/" in link and link.endswith("/"):
                court_index_pages.append(link)
            elif "/pk/" in link and link.endswith(".html") and "resources" not in link:
                court_index_pages.append(link)

        # Step 3: Crawl court-specific index pages for judgment links
        for court_page in court_index_pages:
            if court_page in visited:
                continue
            visited.add(court_page)

            try:
                sub_links = await self._crawl_index_page(court_page)
                for sub_link in sub_links:
                    if sub_link in visited:
                        continue
                    visited.add(sub_link)

                    if JUDGMENT_URL_PATTERN.search(sub_link):
                        judgment_urls.append(sub_link)
                    elif "/pk/" in sub_link and sub_link.endswith("/"):
                        # Year index pages (e.g. /pk/cases/PKSC/2023/)
                        try:
                            year_links = await self._crawl_index_page(sub_link)
                            for year_link in year_links:
                                if year_link not in visited and JUDGMENT_URL_PATTERN.search(year_link):
                                    visited.add(year_link)
                                    judgment_urls.append(year_link)
                        except Exception as exc:
                            logger.warning(
                                "[%s] Failed to crawl year page %s: %s",
                                self.name, sub_link, exc,
                            )
            except Exception as exc:
                logger.warning(
                    "[%s] Failed to crawl court page %s: %s",
                    self.name, court_page, exc,
                )
                continue

        # De-duplicate
        judgment_urls = list(dict.fromkeys(judgment_urls))

        # Fallback: direct search via CommonLII search engine
        if not judgment_urls:
            logger.info("[%s] No URLs from crawl, trying CommonLII search fallback", self.name)
            search_url = (
                "https://www.commonlii.org/cgi-bin/sinosrch.cgi?"
                "mask_path=pk&method=auto&query=trafficking+child+abuse+366-A+370+377"
            )
            try:
                search_links = await self._crawl_index_page(search_url)
                for link in search_links:
                    if JUDGMENT_URL_PATTERN.search(link) and link not in judgment_urls:
                        judgment_urls.append(link)
            except Exception as exc:
                logger.warning("[%s] CommonLII search fallback failed: %s", self.name, exc)

        # Last-resort: try PakistanLawSite search
        if not judgment_urls:
            logger.info("[%s] Trying PakistanLawSite as last-resort", self.name)
            try:
                pls_links = await self._crawl_index_page("https://pakistanlawsite.com/Search")
                for link in pls_links:
                    if link not in judgment_urls:
                        judgment_urls.append(link)
            except Exception as exc:
                logger.warning("[%s] PakistanLawSite fallback failed: %s", self.name, exc)

        judgment_urls = list(dict.fromkeys(judgment_urls))
        self._discovered_urls = judgment_urls

        logger.info(
            "[%s] Discovered %d judgment URLs",
            self.name, len(judgment_urls),
        )
        return judgment_urls

    async def fetch_judgment_html(self, url: str) -> dict[str, Any]:
        """Fetch and parse an individual judgment HTML page.

        CommonLII judgments are in HTML format (not PDF), making
        text extraction straightforward.

        Args:
            url: URL of the judgment page on CommonLII.

        Returns:
            Dict with url, court, date, parties, full_text,
            ppc_sections_mentioned, year, case_number.
        """
        try:
            response = await self.fetch(url, method="GET")
            html = response.text
        except Exception as exc:
            logger.warning("[%s] Failed to fetch judgment %s: %s", self.name, url, exc)
            return {}

        soup = BeautifulSoup(html, "html.parser")

        # Extract title / parties from page title or h1/h2
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        heading = soup.find(["h1", "h2"])
        if heading:
            heading_text = heading.get_text(strip=True)
            if len(heading_text) > len(title):
                title = heading_text

        # Extract main judgment text
        # CommonLII typically puts judgment text in a specific div or just in the body
        content_div = (
            soup.find("div", class_="judgment")
            or soup.find("div", id="judgment")
            or soup.find("div", class_="txt")
            or soup.find("blockquote")
        )
        if content_div:
            full_text = content_div.get_text(" ", strip=True)
        else:
            # Fall back to body text, excluding nav and footer
            for tag in soup.find_all(["nav", "footer", "header", "script", "style"]):
                tag.decompose()
            full_text = soup.get_text(" ", strip=True)

        # Extract court name from URL path
        court = self._resolve_court_name(url)

        # Extract year from URL
        year = self._extract_year_from_url(url)

        # Extract date from text or metadata
        date_decided = ""
        # Look for meta tag with date
        date_meta = soup.find("meta", attrs={"name": "date"})
        if date_meta and date_meta.get("content"):
            date_decided = date_meta["content"]
        else:
            # Search for date patterns in the first portion of text
            date_patterns = [
                r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})",
                r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
                r"(\w+\s+\d{1,2},?\s+\d{4})",
            ]
            header_text = full_text[:1000]
            for pattern in date_patterns:
                match = re.search(pattern, header_text)
                if match:
                    date_decided = match.group(1)
                    break

        # Extract case number from title or text
        case_number = ""
        cn_patterns = [
            r"((?:Civil|Criminal|Constitutional|Writ|Appeal|Petition)\s+(?:No\.?|#)\s*[\w/.-]+\d+)",
            r"(\d{1,4}\s*/\s*\d{4})",
            r"([\w.-]+/[\w.-]+/\d{4})",
        ]
        search_text = f"{title} {full_text[:500]}"
        for pattern in cn_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                case_number = match.group(1).strip()
                break

        # Extract PPC sections from full text
        ppc_sections = extract_ppc_sections(full_text)
        relevant_sections = filter_relevant_sections(ppc_sections)

        # Parse date if found
        parsed_date = parse_pakistani_date(date_decided) if date_decided else None

        return {
            "url": url,
            "pdf_url": url,
            "court": court,
            "case_number": case_number,
            "year": year,
            "title": title,
            "parties": title,
            "date_decided": parsed_date.isoformat() if parsed_date else date_decided,
            "full_text": full_text,
            "ppc_sections": ppc_sections,
            "ppc_sections_relevant": relevant_sections,
            "description": full_text[:500],
        }

    async def search_cases(
        self, year: int, case_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Search CommonLII for Pakistani cases by year.

        Filters the discovered judgment URLs by year, then fetches
        and parses each matching judgment page.

        Args:
            year: Year to filter judgments by.
            case_type: Optional case type filter.

        Returns:
            List of case reference dicts.
        """
        all_urls = await self.discover_judgment_urls()

        # Filter URLs by year
        year_str = str(year)
        year_urls = [
            url for url in all_urls
            if f"/{year_str}/" in url
        ]

        logger.info(
            "[%s] Found %d judgment URLs for year %d",
            self.name, len(year_urls), year,
        )

        cases: list[dict[str, Any]] = []
        for url in year_urls:
            try:
                judgment_data = await self.fetch_judgment_html(url)
                if judgment_data:
                    cases.append(judgment_data)
            except Exception as exc:
                logger.warning(
                    "[%s] Error fetching judgment %s: %s",
                    self.name, url, exc,
                )
                continue

        return cases

    async def download_judgment(
        self, case_ref: dict[str, Any]
    ) -> bytes | None:
        """Download judgment text (HTML, not PDF) from CommonLII.

        CommonLII judgments are HTML pages, not PDFs. This method
        fetches the raw HTML content as bytes.

        Args:
            case_ref: Case reference with CommonLII URL.

        Returns:
            HTML content as bytes, or None.
        """
        url = case_ref.get("url") or case_ref.get("pdf_url")
        if not url:
            return None

        try:
            return await self.fetch_bytes(url)
        except Exception as exc:
            logger.warning(
                "[%s] Failed to download judgment from %s: %s",
                self.name, url, exc,
            )
            return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the CommonLII bulk scraping pipeline.

        Discovers judgment URLs, fetches each judgment page,
        filters for trafficking-related PPC sections, and returns
        structured metadata.

        Returns:
            List of judgment records with extracted metadata.
        """
        logger.info("[%s] Starting CommonLII scrape", self.name)

        # Step 1: Discover all judgment URLs
        all_urls = await self.discover_judgment_urls()
        if not all_urls:
            logger.warning("[%s] No judgment URLs discovered", self.name)
            return []

        # Step 2: Fetch and parse each judgment
        all_judgments: list[dict[str, Any]] = []
        for url in all_urls:
            try:
                judgment_data = await self.fetch_judgment_html(url)
                if not judgment_data:
                    continue

                # Step 3: Filter for relevant PPC sections
                relevant = judgment_data.get("ppc_sections_relevant", [])
                if relevant:
                    metadata = self.extract_metadata(judgment_data)
                    metadata["url"] = url
                    metadata["full_text"] = judgment_data.get("full_text", "")[:5000]

                    # Download and save the HTML content
                    html_bytes = await self.download_judgment(judgment_data)
                    if html_bytes:
                        pdf_path = await self.save_judgment_pdf(judgment_data, html_bytes)
                        metadata["pdf_local_path"] = str(pdf_path)

                    all_judgments.append(metadata)

            except Exception as exc:
                logger.warning(
                    "[%s] Error processing judgment %s: %s",
                    self.name, url, exc,
                )
                continue

        logger.info(
            "[%s] CommonLII scrape complete: %d relevant records from %d total URLs",
            self.name, len(all_judgments), len(all_urls),
        )
        return all_judgments

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a CommonLII judgment record.

        Args:
            record: A judgment record dictionary.

        Returns:
            True if required fields are present.
        """
        required_fields = ["url", "court", "full_text"]
        return all(record.get(f) for f in required_fields)
