"""Ministry of Human Rights (MoHR) ZARRA report checker.

Monitors mohr.gov.pk for new ZARRA PDF publications.

URL pattern: https://mohr.gov.pk/SiteImage/Misc/files/ZARRA*
Schedule: Monthly (0 3 25 * *)
Priority: P1
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class MoHRChecker(BaseScraper):
    """Checker for new MoHR ZARRA publications."""

    name: str = "mohr_checker"
    source_url: str = "https://mohr.gov.pk"
    pdf_pattern: str = "https://mohr.gov.pk/SiteImage/Misc/files/ZARRA"
    schedule: str = "0 3 25 * *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    KNOWN_REPORT_PATTERNS: list[str] = [
        "ZARRA_2019",
        "ZARRA_2020",
        "ZARRA_2021",
        "ZARRA_2022",
        "ZARRA_2023",
        "ZARRA_2024",
    ]

    # Known URL patterns to probe
    PDF_EXTENSIONS: list[str] = [".pdf", ".PDF"]
    URL_TEMPLATES: list[str] = [
        "https://mohr.gov.pk/SiteImage/Misc/files/{name}.pdf",
        "https://mohr.gov.pk/SiteImage/Misc/files/{name}.PDF",
        "https://mohr.gov.pk/uploads/{name}.pdf",
        "https://mohr.gov.pk/Detail/{name}",
    ]

    async def scan_for_pdfs(self) -> list[str]:
        """Scan MoHR site for ZARRA PDF URLs."""
        discovered_urls: list[str] = []
        client = await self.get_client()

        # Probe known URL patterns with year suffixes
        for pattern_name in self.KNOWN_REPORT_PATTERNS:
            for template in self.URL_TEMPLATES:
                url = template.format(name=pattern_name)
                try:
                    response = await client.head(url, follow_redirects=True)
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
                            discovered_urls.append(url)
                            logger.info("[%s] Found ZARRA PDF: %s", self.name, url)
                            break
                except Exception:
                    continue

        # Also scan the MoHR publications page for links
        try:
            for page_path in ["/", "/Detail/PublicationReport", "/publications"]:
                try:
                    response = await self.fetch(f"{self.source_url}{page_path}")
                    soup = BeautifulSoup(response.text, "lxml")
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        text = link.get_text(strip=True).lower()
                        if "zarra" in href.lower() or "zarra" in text:
                            full_url = href if href.startswith("http") else f"{self.source_url}/{href.lstrip('/')}"
                            if full_url not in discovered_urls:
                                discovered_urls.append(full_url)
                except Exception:
                    continue
        except Exception as exc:
            logger.warning("[%s] Error scanning pages: %s", self.name, exc)

        return discovered_urls

    async def check_for_new(
        self, known_urls: set[str] | None = None
    ) -> list[str]:
        """Identify new ZARRA PDFs not previously downloaded."""
        known = known_urls or set()
        all_urls = await self.scan_for_pdfs()
        return [url for url in all_urls if url not in known]

    async def download_report(self, pdf_url: str) -> bytes | None:
        """Download a ZARRA PDF report."""
        try:
            return await self.fetch_bytes(pdf_url)
        except Exception as exc:
            logger.error("[%s] Failed to download %s: %s", self.name, pdf_url, exc)
            return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the MoHR ZARRA publication check."""
        pdf_urls = await self.scan_for_pdfs()
        logger.info("[%s] Discovered %d ZARRA URLs", self.name, len(pdf_urls))

        results: list[dict[str, Any]] = []
        raw_dir = self.get_raw_dir() / "pdfs"
        raw_dir.mkdir(parents=True, exist_ok=True)

        for url in pdf_urls:
            record: dict[str, Any] = {
                "pdf_url": url,
                "source": self.name,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

            # Extract year from URL
            for year_str in ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]:
                if year_str in url:
                    record["year"] = int(year_str)
                    break

            # Download the PDF
            try:
                pdf_bytes = await self.download_report(url)
                if pdf_bytes:
                    filename = Path(url).name or f"zarra_{self.run_id}.pdf"
                    pdf_path = raw_dir / filename
                    pdf_path.write_bytes(pdf_bytes)
                    record["local_path"] = str(pdf_path)
                    record["file_size_bytes"] = len(pdf_bytes)
            except Exception as exc:
                logger.warning("[%s] Could not download %s: %s", self.name, url, exc)

            results.append(record)

        return results

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a ZARRA publication record."""
        return bool(record.get("pdf_url"))
