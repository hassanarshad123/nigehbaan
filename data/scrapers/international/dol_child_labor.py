"""US Department of Labor ILAB child labor report scraper.

URL: https://www.dol.gov/agencies/ilab/resources/reports/child-labor/pakistan
Schedule: Annually (0 3 15 10 *)
Priority: P1

Updated 2026-03-22: Fixed to handle DOL API / page format changes.
- Multiple URL patterns for the Pakistan country page
- Updated hardcoded PDF probe paths to current DOL file structure
- Added ILAB API endpoint as primary source
- Added Firecrawl + direct fetch dual strategy
- All records now use statistical_reports format with source_name
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import re

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DOLChildLaborScraper(BaseScraper):
    """Scraper for US DOL ILAB child labor reports on Pakistan."""

    name: str = "dol_child_labor"
    source_url: str = (
        "https://www.dol.gov/agencies/ilab/resources/reports/"
        "child-labor/pakistan"
    )
    schedule: str = "0 3 15 10 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0
    request_timeout: float = 60.0
    use_firecrawl: bool = True  # DOL is behind Cloudflare JS challenge

    # DOL ILAB API endpoint (returns JSON when available)
    ILAB_API_URL: str = (
        "https://www.dol.gov/agencies/ilab/api/reports/child-labor"
    )

    # Alternative page URLs in case DOL restructures
    ALTERNATIVE_URLS: list[str] = [
        "https://www.dol.gov/agencies/ilab/resources/reports/child-labor/pakistan",
        "https://www.dol.gov/agencies/ilab/resources/reports/child-labor/findings/pakistan",
        "https://www.dol.gov/agencies/ilab/explore-our-data/pakistan",
    ]

    # Known PDF URL patterns — DOL has used several structures
    PDF_URL_PATTERNS: list[str] = [
        # Current pattern (2023+)
        "https://www.dol.gov/sites/dolgov/files/ILAB/child_labor/tda{year}/Pakistan.pdf",
        # Alternative patterns
        "https://www.dol.gov/sites/dolgov/files/ILAB/child_labor/{year}/Pakistan.pdf",
        "https://www.dol.gov/sites/dolgov/files/ILAB/child_labor/TDA{year}/Pakistan.pdf",
        "https://www.dol.gov/sites/dolgov/files/ILAB/child_labor/N_TDA_{year}/Pakistan.pdf",
        "https://www.dol.gov/sites/dolgov/files/ILAB/{year}-findings-on-the-worst-forms-of-child-labor/pakistan.pdf",
    ]

    async def _try_ilab_api(self) -> list[dict[str, Any]]:
        """Try the DOL ILAB API for structured child labor data."""
        reports: list[dict[str, Any]] = []
        scraped_at = datetime.now(timezone.utc).isoformat()

        try:
            response = await self.fetch(
                self.ILAB_API_URL,
                params={"country": "Pakistan", "format": "json"},
                headers={"Accept": "application/json"},
            )
            data = response.json()

            items = data if isinstance(data, list) else data.get("data", data.get("results", []))
            for item in items:
                year = item.get("year") or item.get("Year")
                title = (
                    item.get("title")
                    or item.get("name")
                    or f"Pakistan Child Labor Findings {year}"
                )
                pdf_url = item.get("pdf_url") or item.get("report_url") or ""
                if pdf_url and not pdf_url.startswith("http"):
                    pdf_url = f"https://www.dol.gov{pdf_url}"

                reports.append({
                    "source_name": "DOL_ILAB",
                    "report_title": title,
                    "indicator": "child_labor_findings",
                    "pdf_url": pdf_url,
                    "year": int(year) if year else None,
                    "is_pdf": pdf_url.lower().endswith(".pdf") if pdf_url else False,
                    "country": "Pakistan",
                    "source": self.name,
                    "source_url": self.source_url,
                    "scraped_at": scraped_at,
                })
            logger.info("[%s] ILAB API returned %d records", self.name, len(reports))
        except Exception as exc:
            logger.info(
                "[%s] ILAB API not available (%s) — falling back to page scrape",
                self.name, exc,
            )
        return reports

    async def fetch_country_page(self) -> str:
        """Fetch the DOL ILAB Pakistan country page.

        Tries the primary URL and alternatives until one succeeds.
        """
        for url in self.ALTERNATIVE_URLS:
            try:
                response = await self.fetch(url)
                if response.text and len(response.text) > 500:
                    logger.info("[%s] Fetched country page from %s", self.name, url)
                    return response.text
            except Exception as exc:
                logger.debug("[%s] URL %s failed: %s", self.name, url, exc)
        return ""

    def extract_report_links(self, html: str) -> list[dict[str, Any]]:
        """Extract annual report PDF links from the country page.

        Handles both the old DOL page structure and the newer format
        where reports are in cards, accordions, or list items.
        """
        soup = BeautifulSoup(html, "lxml")
        reports: list[dict[str, Any]] = []
        scraped_at = datetime.now(timezone.utc).isoformat()

        # Search all <a> tags for relevant links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)

            is_pdf = href.lower().endswith(".pdf")
            is_report = any(
                kw in text.lower() or kw in href.lower()
                for kw in ["finding", "report", "child labor", "child labour", "pakistan", "tda"]
            )

            if is_pdf or (is_report and href):
                full_url = (
                    href if href.startswith("http") else f"https://www.dol.gov{href}"
                )

                # Extract year from text or URL
                year = None
                year_match = re.search(r"20[0-2]\d", text) or re.search(
                    r"20[0-2]\d", href
                )
                if year_match:
                    year = int(year_match.group())

                reports.append({
                    "source_name": "DOL_ILAB",
                    "report_title": text or f"DOL Child Labor Report {year or 'unknown'}",
                    "indicator": "child_labor_findings",
                    "pdf_url": full_url,
                    "year": year,
                    "is_pdf": is_pdf,
                    "country": "Pakistan",
                    "source": self.name,
                    "source_url": self.source_url,
                    "scraped_at": scraped_at,
                })

        # Fallback: also check JSON-LD or meta tags for structured data
        if not reports:
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    import json
                    ld_data = json.loads(script.string or "")
                    items = ld_data if isinstance(ld_data, list) else [ld_data]
                    for item in items:
                        if item.get("@type") in ("Report", "CreativeWork", "Dataset"):
                            url = item.get("url", "")
                            name = item.get("name", "")
                            if url:
                                reports.append({
                                    "source_name": "DOL_ILAB",
                                    "report_title": name,
                                    "indicator": "child_labor_findings",
                                    "pdf_url": url,
                                    "year": None,
                                    "is_pdf": url.lower().endswith(".pdf"),
                                    "country": "Pakistan",
                                    "source": self.name,
                                    "source_url": self.source_url,
                                    "scraped_at": scraped_at,
                                })
                except Exception:
                    continue

        # Deduplicate by URL
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for r in reports:
            key = r["pdf_url"]
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique

    async def download_report(self, pdf_url: str) -> bytes | None:
        """Download a DOL child labor report PDF."""
        try:
            return await self.fetch_bytes(pdf_url)
        except Exception as exc:
            logger.error("[%s] Failed to download %s: %s", self.name, pdf_url, exc)
            return None

    async def _probe_known_pdf_urls(self) -> list[dict[str, Any]]:
        """Probe known PDF URL patterns with GET + Range header."""
        reports: list[dict[str, Any]] = []
        scraped_at = datetime.now(timezone.utc).isoformat()
        client = await self.get_client()

        for year in range(2018, 2027):
            for pattern in self.PDF_URL_PATTERNS:
                pdf_url = pattern.format(year=year)
                try:
                    probe = await client.get(
                        pdf_url,
                        follow_redirects=True,
                        headers={"Range": "bytes=0-0"},
                    )
                    if probe.status_code in (200, 206):
                        reports.append({
                            "source_name": "DOL_ILAB",
                            "report_title": f"Pakistan Child Labor Report {year}",
                            "indicator": "child_labor_findings",
                            "pdf_url": pdf_url,
                            "year": year,
                            "is_pdf": True,
                            "country": "Pakistan",
                            "source": self.name,
                            "source_url": self.source_url,
                            "scraped_at": scraped_at,
                        })
                        logger.info("[%s] Probe found: %s", self.name, pdf_url)
                        break  # Found this year, skip other patterns
                except Exception:
                    continue

        return reports

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the DOL ILAB scraping pipeline.

        Strategy order:
        1. ILAB API (structured JSON)
        2. Firecrawl-rendered page scrape
        3. Direct HTML fetch + parse
        4. Hardcoded PDF URL probing
        """
        # Strategy 1: Try the ILAB API first
        reports = await self._try_ilab_api()

        # Strategy 2: Firecrawl-rendered page (JS-rendered, bypasses Cloudflare)
        if not reports and self.use_firecrawl:
            try:
                fc_result = await self.fetch_via_firecrawl(self.source_url)
                html = fc_result.html if fc_result.success else ""
                if html:
                    reports = self.extract_report_links(html)
            except Exception as exc:
                logger.warning("[%s] Firecrawl scrape failed: %s", self.name, exc)

        # Strategy 3: Direct HTML fetch from multiple URLs
        if not reports:
            html = await self.fetch_country_page()
            if html:
                reports = self.extract_report_links(html)
            logger.info("[%s] Found %d report links from page", self.name, len(reports))

        # Strategy 4: Probe known PDF URL patterns
        if not reports:
            logger.info("[%s] Probing known PDF URL patterns via GET", self.name)
            reports = await self._probe_known_pdf_urls()

        if not reports:
            logger.warning(
                "[%s] All strategies exhausted — returning empty list", self.name
            )
            return []

        # Download PDFs for reports that have PDF URLs
        raw_dir = self.get_raw_dir() / "pdfs"
        raw_dir.mkdir(parents=True, exist_ok=True)

        for report in reports:
            if report.get("is_pdf") and report.get("pdf_url"):
                try:
                    pdf_bytes = await self.download_report(report["pdf_url"])
                    if pdf_bytes:
                        filename = (
                            Path(report["pdf_url"]).name
                            or f"dol_{report.get('year', 'unknown')}.pdf"
                        )
                        pdf_path = raw_dir / filename
                        pdf_path.write_bytes(pdf_bytes)
                        report["local_path"] = str(pdf_path)
                except Exception as exc:
                    logger.warning("[%s] Could not save PDF: %s", self.name, exc)

        logger.info("[%s] Returning %d reports total", self.name, len(reports))
        return reports

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a DOL report record."""
        return bool(record.get("year") or record.get("pdf_url"))
