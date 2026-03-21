"""Provincial Labour Force Surveys scraper for child labor data.

Scrapes Pakistan Bureau of Statistics and provincial bureau sites for
labour force survey PDFs containing district-level child labor
breakdowns by province, gender, and urban/rural classification.

Sources:
  - PBS: https://www.pbs.gov.pk/content/labour-force-survey
  - Punjab BOS: https://bos.gop.pk/
  - Sindh BOS: https://sindhbos.gov.pk/
  - KP BOS: https://kpbos.gov.pk/

Schedule: Annually (0 6 1 7 *)
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

# Provincial bureau URLs mapped by province name
_PROVINCIAL_SOURCES: dict[str, str] = {
    "Punjab": "https://bos.gop.pk/",
    "Sindh": "https://sindhbos.gov.pk/",
    "Khyber Pakhtunkhwa": "https://kpbos.gov.pk/",
}

# Keywords that identify child-labor-relevant PDFs
_CHILD_LABOR_KEYWORDS: list[str] = [
    "child lab",
    "child work",
    "labour force",
    "labor force",
    "lfs",
    "economically active children",
    "working children",
    "employed children",
    "child employment",
    "district",
    "survey",
]

# Province detection patterns
_PROVINCES: list[str] = [
    "Punjab",
    "Sindh",
    "Khyber Pakhtunkhwa",
    "Balochistan",
    "Islamabad Capital Territory",
]

_PROVINCE_ABBREVIATIONS: dict[str, str] = {
    "kp": "Khyber Pakhtunkhwa",
    "kpk": "Khyber Pakhtunkhwa",
    "ict": "Islamabad Capital Territory",
    "gb": "Gilgit-Baltistan",
    "ajk": "Azad Jammu & Kashmir",
}


class ProvincialLabourSurveysScraper(BaseScraper):
    """Scraper for provincial labour force survey child labor data.

    Fetches the PBS national labour force survey page and three
    provincial bureau of statistics sites, discovers PDF links,
    downloads relevant PDFs, and extracts child labor statistics
    with province-level geographic scope.

    URL: https://www.pbs.gov.pk/content/labour-force-survey
    Schedule: Annually
    Priority: P1
    """

    name: str = "provincial_labour_surveys"
    source_url: str = "https://www.pbs.gov.pk/content/labour-force-survey"
    schedule: str = "0 6 1 7 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0
    request_timeout: float = 90.0

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

    def _discover_pdf_links(
        self, html: str, base_url: str
    ) -> list[dict[str, str]]:
        """Parse HTML page for PDF links related to labour surveys.

        Args:
            html: Raw HTML content.
            base_url: Base URL for resolving relative links.

        Returns:
            List of dicts with keys: title, pdf_url.
        """
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []
        seen: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            parent_text = ""
            if link.parent:
                parent_text = link.parent.get_text(strip=True)

            combined_text = f"{text} {parent_text} {href}".lower()

            # Must be a PDF or contain labour-related keywords
            is_pdf = ".pdf" in href.lower()
            is_relevant = any(
                kw in combined_text for kw in _CHILD_LABOR_KEYWORDS
            )

            if not (is_pdf and is_relevant):
                # Also accept non-PDF links that strongly suggest survey reports
                if not (is_relevant and ("report" in combined_text or "survey" in combined_text)):
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

            title = text if text else href.split("/")[-1]
            results.append({"title": title.strip(), "pdf_url": full_url})

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

    def _detect_province(self, text: str) -> str | None:
        """Detect a province name from text.

        Args:
            text: Text to search for province references.

        Returns:
            Standardized province name or None.
        """
        text_lower = text.lower()
        for province in _PROVINCES:
            if province.lower() in text_lower:
                return province
        for abbrev, full_name in _PROVINCE_ABBREVIATIONS.items():
            if re.search(rf"\b{abbrev}\b", text_lower):
                return full_name
        return None

    async def _extract_pdf_metadata(
        self, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Download a PDF and extract child labor statistics.

        Args:
            pdf_url: URL of the PDF file.

        Returns:
            List of statistical_reports records extracted from the PDF.
        """
        try:
            import pdfplumber
        except ImportError:
            logger.warning(
                "[%s] pdfplumber not installed, returning link-only record",
                self.name,
            )
            return []

        raw_dir = self.get_raw_dir()
        filename = pdf_url.split("/")[-1].split("?")[0]
        if not filename.endswith(".pdf"):
            filename = f"pls_{self.run_id}.pdf"
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

        return self._parse_text_for_stats(text, pdf_url)

    def _parse_text_for_stats(
        self, text: str, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Extract child labor statistics from PDF text.

        Searches for percentage patterns and province references.

        Args:
            text: Extracted PDF text.
            pdf_url: Source URL for provenance.

        Returns:
            List of statistical_reports records.
        """
        records: list[dict[str, Any]] = []
        year = self._extract_year(pdf_url) or datetime.now(timezone.utc).year
        now = datetime.now(timezone.utc).isoformat()

        # Pattern: "X.X% children" or "X.X percent" in child labor context
        pct_pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*%?\s*(?:children|child|working\s+children|"
            r"economically\s+active)",
            re.IGNORECASE,
        )

        for match in pct_pattern.finditer(text):
            start = max(0, match.start() - 150)
            context = text[start:match.end() + 80].strip()

            province = self._detect_province(context)

            records.append({
                "source_name": self.name,
                "report_year": year,
                "report_title": f"Labour Force Survey {year}",
                "indicator": "child_labor_prevalence",
                "value": float(match.group(1)),
                "unit": "percent",
                "geographic_scope": province or "Pakistan",
                "pdf_url": pdf_url,
                "extraction_method": "pdf_text_regex",
                "extraction_confidence": 0.50,
                "victim_age_bracket": "5-17",
                "scraped_at": now,
            })

        # Pattern: absolute numbers like "1,234 children working"
        count_pattern = re.compile(
            r"(\d{1,3}(?:,\d{3})*)\s*(?:children|child workers|working\s+children)",
            re.IGNORECASE,
        )

        for match in count_pattern.finditer(text):
            start = max(0, match.start() - 150)
            context = text[start:match.end() + 80].strip()

            province = self._detect_province(context)
            raw_value = match.group(1).replace(",", "")

            records.append({
                "source_name": self.name,
                "report_year": year,
                "report_title": f"Labour Force Survey {year}",
                "indicator": "child_labor_count",
                "value": int(raw_value),
                "unit": "count",
                "geographic_scope": province or "Pakistan",
                "pdf_url": pdf_url,
                "extraction_method": "pdf_text_regex",
                "extraction_confidence": 0.45,
                "victim_age_bracket": "5-17",
                "scraped_at": now,
            })

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch PBS and provincial bureau pages, discover and process PDFs.

        Checks the national PBS page first, then each provincial bureau
        site. Gracefully continues if individual sites are unreachable.

        Returns:
            List of statistical_reports records.
        """
        all_pdf_links: list[dict[str, str]] = []
        province_for_url: dict[str, str] = {}

        # 1. Fetch national PBS page
        html = await self._fetch_page(self.source_url)
        if html:
            links = self._discover_pdf_links(html, self.source_url)
            all_pdf_links.extend(links)
            logger.info(
                "[%s] Found %d links on PBS national page",
                self.name, len(links),
            )
        else:
            logger.warning("[%s] Could not fetch PBS national page", self.name)

        # 2. Fetch provincial bureau pages
        for province, bureau_url in _PROVINCIAL_SOURCES.items():
            html = await self._fetch_page(bureau_url)
            if html:
                links = self._discover_pdf_links(html, bureau_url)
                for link in links:
                    province_for_url[link["pdf_url"]] = province
                all_pdf_links.extend(links)
                logger.info(
                    "[%s] Found %d links on %s BOS page",
                    self.name, len(links), province,
                )
            else:
                logger.warning(
                    "[%s] Could not fetch %s BOS page at %s",
                    self.name, province, bureau_url,
                )

        # Deduplicate by URL
        seen: set[str] = set()
        unique_links: list[dict[str, str]] = []
        for link in all_pdf_links:
            if link["pdf_url"] not in seen:
                seen.add(link["pdf_url"])
                unique_links.append(link)

        if not unique_links:
            logger.warning("[%s] No relevant PDF links found", self.name)
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
            year = self._extract_year(f"{title} {pdf_url}")

            # Determine province from source site or title
            province = province_for_url.get(pdf_url)
            if not province:
                province = self._detect_province(f"{title} {pdf_url}")

            # Always create a link-level record
            base_record = {
                "source_name": self.name,
                "report_year": year or datetime.now(timezone.utc).year,
                "report_title": title,
                "indicator": "labour_force_survey_report",
                "value": None,
                "unit": "report",
                "geographic_scope": province or "Pakistan",
                "pdf_url": pdf_url,
                "extraction_method": "pdf_link",
                "extraction_confidence": 0.60,
                "scraped_at": now,
            }

            # Try to extract statistics from the PDF
            if pdf_url.lower().endswith(".pdf"):
                try:
                    pdf_records = await self._extract_pdf_metadata(pdf_url)
                    if pdf_records:
                        # Apply province override if we know the source
                        for rec in pdf_records:
                            if province and rec.get("geographic_scope") == "Pakistan":
                                rec["geographic_scope"] = province
                        all_records.extend(pdf_records)
                        continue  # Skip the base record if we got detailed ones
                except Exception as exc:
                    logger.warning(
                        "[%s] PDF extraction failed for %s: %s",
                        self.name, pdf_url, exc,
                    )

            all_records.append(base_record)

        logger.info("[%s] Total records: %d", self.name, len(all_records))
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a provincial labour survey record.

        Requires source_name, report_title, and geographic_scope.

        Args:
            record: Dictionary representing one scraped record.

        Returns:
            True if the record passes validation.
        """
        return bool(
            record.get("source_name")
            and record.get("report_title")
            and record.get("geographic_scope")
        )
