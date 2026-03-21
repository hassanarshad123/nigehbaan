"""US Department of Labor ILAB child labor report scraper.

URL: https://www.dol.gov/agencies/ilab/resources/reports/child-labor/pakistan
Schedule: Annually (0 3 15 10 *)
Priority: P1
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

    async def fetch_country_page(self) -> str:
        """Fetch the DOL ILAB Pakistan country page."""
        response = await self.fetch(self.source_url)
        return response.text

    def extract_report_links(self, html: str) -> list[dict[str, Any]]:
        """Extract annual report PDF links from the country page."""
        soup = BeautifulSoup(html, "lxml")
        reports: list[dict[str, Any]] = []

        # Primary: search all <a> tags
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)

            is_pdf = href.lower().endswith(".pdf")
            is_report = any(
                kw in text.lower() or kw in href.lower()
                for kw in ["finding", "report", "child labor", "pakistan"]
            )

            if is_pdf or (is_report and href):
                full_url = href if href.startswith("http") else f"https://www.dol.gov{href}"

                # Extract year from text or URL
                year = None
                year_match = re.search(r"20[0-2]\d", text) or re.search(r"20[0-2]\d", href)
                if year_match:
                    year = int(year_match.group())

                reports.append({
                    "title": text,
                    "pdf_url": full_url,
                    "year": year,
                    "is_pdf": is_pdf,
                    "source": self.name,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })

        # Fallback: search for links inside article/section/div containers
        if not reports:
            for container in soup.find_all(["article", "section", "div"]):
                for link in container.find_all("a", href=True):
                    href = link["href"]
                    text = link.get_text(strip=True)
                    combined = f"{text} {href}".lower()
                    if any(kw in combined for kw in ["finding", "report", "child labor", "pakistan", ".pdf"]):
                        full_url = href if href.startswith("http") else f"https://www.dol.gov{href}"
                        year = None
                        year_match = re.search(r"20[0-2]\d", text) or re.search(r"20[0-2]\d", href)
                        if year_match:
                            year = int(year_match.group())
                        reports.append({
                            "title": text,
                            "pdf_url": full_url,
                            "year": year,
                            "is_pdf": href.lower().endswith(".pdf"),
                            "source": self.name,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                        })

        # Deduplicate by URL
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for r in reports:
            if r["pdf_url"] not in seen:
                seen.add(r["pdf_url"])
                unique.append(r)

        return unique

    async def download_report(self, pdf_url: str) -> bytes | None:
        """Download a DOL child labor report PDF."""
        try:
            return await self.fetch_bytes(pdf_url)
        except Exception as exc:
            logger.error("[%s] Failed to download %s: %s", self.name, pdf_url, exc)
            return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the DOL ILAB scraping pipeline."""
        # Try Firecrawl first (JS-rendered page), then direct fetch
        if self.use_firecrawl:
            fc_result = await self.fetch_via_firecrawl(self.source_url)
            html = fc_result.html if fc_result.success else ""
        else:
            try:
                html = await self.fetch_country_page()
            except Exception:
                html = ""

        reports = self.extract_report_links(html) if html else []
        logger.info("[%s] Found %d report links from page", self.name, len(reports))

        # Hardcoded PDF URL fallback — DOL blocks HEAD so use GET with stream
        if not reports:
            logger.info("[%s] Probing known PDF URL patterns via GET", self.name)
            client = await self.get_client()
            for year in range(2018, 2026):
                pdf_url = f"https://www.dol.gov/sites/dolgov/files/ILAB/child_labor/tda{year}/Pakistan.pdf"
                try:
                    probe = await client.get(
                        pdf_url,
                        follow_redirects=True,
                        headers={"Range": "bytes=0-0"},
                    )
                    if probe.status_code in (200, 206):
                        reports.append({
                            "title": f"Pakistan Child Labor Report {year}",
                            "pdf_url": pdf_url,
                            "year": year,
                            "is_pdf": True,
                            "source": self.name,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                        })
                        logger.info("[%s] Hardcoded probe found: %s", self.name, pdf_url)
                except Exception:
                    continue

        raw_dir = self.get_raw_dir() / "pdfs"
        raw_dir.mkdir(parents=True, exist_ok=True)

        for report in reports:
            if report.get("is_pdf") and report.get("pdf_url"):
                try:
                    pdf_bytes = await self.download_report(report["pdf_url"])
                    if pdf_bytes:
                        filename = Path(report["pdf_url"]).name or f"dol_{report.get('year', 'unknown')}.pdf"
                        pdf_path = raw_dir / filename
                        pdf_path.write_bytes(pdf_bytes)
                        report["local_path"] = str(pdf_path)
                except Exception as exc:
                    logger.warning("[%s] Could not save PDF: %s", self.name, exc)

        return reports

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a DOL report record."""
        return bool(record.get("year") or record.get("pdf_url"))
