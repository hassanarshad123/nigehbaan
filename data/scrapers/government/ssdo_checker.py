"""SSDO (Society for the Protection of the Rights of the Child) checker.

Monitors ssdo.org.pk for new reports and publications on child protection.

URL: https://ssdo.org.pk
Schedule: Monthly (0 3 20 * *)
Priority: P1
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SSDOChecker(BaseScraper):
    """Checker for new SSDO publications on child protection."""

    name: str = "ssdo_checker"
    source_url: str = "https://ssdo.org.pk"
    schedule: str = "0 3 20 * *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    # Known sections to scan for publications
    PUBLICATION_PATHS: list[str] = [
        "/publications",
        "/reports",
        "/resources",
        "/",
    ]

    async def is_site_available(self) -> bool:
        """Check if ssdo.org.pk responds at all."""
        try:
            client = await self.get_client()
            response = await client.head(self.source_url, follow_redirects=True)
            return response.status_code < 500
        except Exception:
            return False

    async def fetch_publications_page(self) -> str:
        """Fetch the SSDO publications/reports page.

        Falls back to Wayback Machine if the live site is down.
        """
        # Try live site first
        for path in self.PUBLICATION_PATHS:
            url = f"{self.source_url}{path}"
            try:
                response = await self.fetch(url)
                if response.status_code == 200:
                    return response.text
            except Exception:
                continue

        # Wayback Machine fallback
        logger.info("[%s] Live site failed, trying Wayback Machine", self.name)
        for path in self.PUBLICATION_PATHS:
            wayback_url = f"https://web.archive.org/web/2024/https://ssdo.org.pk{path}"
            try:
                response = await self.fetch(wayback_url)
                if response.status_code == 200 and len(response.text) > 500:
                    logger.info("[%s] Wayback fallback succeeded for %s", self.name, path)
                    return response.text
            except Exception:
                continue

        return ""

    def parse_publication_links(
        self, html: str
    ) -> list[dict[str, Any]]:
        """Parse publication links and metadata from the page."""
        soup = BeautifulSoup(html, "lxml")
        publications: list[dict[str, Any]] = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            title = link.get_text(strip=True)

            is_pdf = href.lower().endswith(".pdf")
            is_report = any(
                kw in title.lower() or kw in href.lower()
                for kw in ["report", "child", "protection", "cruel", "annual", "ssdo"]
            )

            if is_pdf or is_report:
                full_url = href if href.startswith("http") else f"{self.source_url}/{href.lstrip('/')}"
                pub = {
                    "title": title or Path(href).stem,
                    "pdf_url": full_url,
                    "is_pdf": is_pdf,
                    "source": self.name,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }

                # Try to extract date from parent element
                parent = link.parent
                if parent:
                    date_el = parent.find("time")
                    if date_el:
                        pub["published_date"] = date_el.get("datetime", date_el.get_text(strip=True))
                    else:
                        span = parent.find("span", class_=lambda x: x and "date" in str(x).lower())
                        if span:
                            pub["published_date"] = span.get_text(strip=True)

                publications.append(pub)

        return publications

    async def check_for_new(
        self, known_urls: set[str] | None = None
    ) -> list[dict[str, Any]]:
        """Check for publications not in the known set."""
        known = known_urls or set()
        html = await self.fetch_publications_page()
        if not html:
            return []
        publications = self.parse_publication_links(html)
        return [p for p in publications if p.get("pdf_url") not in known]

    async def download_report(self, pdf_url: str) -> bytes | None:
        """Download a PDF report from SSDO."""
        try:
            return await self.fetch_bytes(pdf_url)
        except Exception as exc:
            logger.error("[%s] Failed to download %s: %s", self.name, pdf_url, exc)
            return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the SSDO publication check.

        Returns empty list gracefully if both live and Wayback fail.
        """
        html = await self.fetch_publications_page()
        if not html:
            logger.warning(
                "[%s] Could not fetch publications page (live or Wayback)",
                self.name,
            )
            return []

        publications = self.parse_publication_links(html)
        logger.info("[%s] Found %d publications", self.name, len(publications))

        # Download PDFs to raw storage
        raw_dir = self.get_raw_dir() / "pdfs"
        raw_dir.mkdir(parents=True, exist_ok=True)

        for pub in publications:
            if pub.get("is_pdf") and pub.get("pdf_url"):
                try:
                    pdf_bytes = await self.download_report(pub["pdf_url"])
                    if pdf_bytes:
                        filename = Path(pub["pdf_url"]).name or f"ssdo_report_{self.run_id}.pdf"
                        pdf_path = raw_dir / filename
                        pdf_path.write_bytes(pdf_bytes)
                        pub["local_path"] = str(pdf_path)
                        logger.info("[%s] Downloaded: %s", self.name, filename)
                except Exception as exc:
                    logger.warning("[%s] Failed to save PDF: %s", self.name, exc)

        return publications

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an SSDO publication record."""
        return bool(record.get("title") and record.get("pdf_url"))
