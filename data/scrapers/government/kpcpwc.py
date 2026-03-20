"""KP Child Protection & Welfare Commission (KPCPWC) scraper.

Scrapes kpcpwc.gov.pk for child protection facts and figures.

URL: https://kpcpwc.gov.pk/factsandfigure.html
Schedule: Monthly (0 3 10 * *)
Priority: P1
"""

from datetime import datetime, timezone
from typing import Any

import logging

from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class KPCPWCScraper(BaseScraper):
    """Scraper for KP Child Protection & Welfare Commission."""

    name: str = "kpcpwc"
    source_url: str = "https://kpcpwc.gov.pk/factsandfigure.html"
    schedule: str = "0 3 10 * *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0

    async def fetch_facts_page(self) -> str:
        """Fetch the KPCPWC facts and figures page."""
        response = await self.fetch(self.source_url)
        return response.text

    def parse_statistics(self, html: str) -> list[dict[str, Any]]:
        """Parse statistical data from the facts page."""
        soup = BeautifulSoup(html, "lxml")
        records: list[dict[str, Any]] = []

        # Parse data tables
        for table in soup.find_all("table"):
            headers: list[str] = [
                th.get_text(strip=True) for th in table.find_all("th")
            ]
            if not headers:
                first_row = table.find("tr")
                if first_row:
                    headers = [
                        c.get_text(strip=True)
                        for c in first_row.find_all(["th", "td"])
                    ]

            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if not cells or len(cells) < 2:
                    continue
                record = dict(zip(headers, cells)) if headers and len(headers) >= len(cells) else {
                    f"col_{i}": c for i, c in enumerate(cells)
                }
                record["province"] = "Khyber Pakhtunkhwa"
                record["source"] = self.name
                record["scraped_at"] = datetime.now(timezone.utc).isoformat()
                records.append(record)

        # Parse infographic/stat blocks (divs with numbers)
        for stat_block in soup.find_all(["div", "section"], class_=lambda x: x and any(
            kw in str(x).lower() for kw in ["stat", "fact", "figure", "count", "number"]
        )):
            heading = stat_block.find(["h2", "h3", "h4", "strong"])
            value_el = stat_block.find(["span", "p", "div"], class_=lambda x: x and "number" in str(x).lower())
            if heading and value_el:
                records.append({
                    "category": heading.get_text(strip=True),
                    "value": value_el.get_text(strip=True),
                    "province": "Khyber Pakhtunkhwa",
                    "source": self.name,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })

        # Extract any linked PDFs/reports
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.lower().endswith(".pdf"):
                records.append({
                    "record_type": "report_link",
                    "title": link.get_text(strip=True),
                    "pdf_url": href if href.startswith("http") else f"https://kpcpwc.gov.pk/{href.lstrip('/')}",
                    "province": "Khyber Pakhtunkhwa",
                    "source": self.name,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })

        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the KPCPWC scraping pipeline."""
        html = await self.fetch_facts_page()
        return self.parse_statistics(html)

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a KPCPWC record."""
        return bool(record.get("source"))
