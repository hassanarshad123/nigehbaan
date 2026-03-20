"""Brookings Institution Pakistani brides report scraper.

Scrapes the Brookings article and associated PDF on 629 Pakistani
girls sold as brides to Chinese men. Extracts key statistics,
findings, and structured data from the report.

Source: https://www.brookings.edu/articles/pakistani-brides/
Schedule: One-time (manual trigger)
Priority: P2 — Key research reference on cross-border trafficking
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import logging
import re

from bs4 import BeautifulSoup

from data.scrapers.base_pdf_scraper import BasePDFReportScraper

logger = logging.getLogger(__name__)

# Key statistics to extract from the report text
_STAT_PATTERNS: list[tuple[str, str]] = [
    (r"(\d[\d,]*)\s*(?:Pakistani\s+)?(?:girls?|women|brides?)\s+(?:sold|trafficked|married)", "victims_count"),
    (r"(\d[\d,]*)\s*(?:Chinese\s+)?(?:men|grooms?|husbands?)", "perpetrators_count"),
    (r"(?:between|from)\s+(\d{4})\s*(?:and|to|-)\s*(\d{4})", "year_range"),
    (r"(\d[\d,]*)\s*(?:FIRs?|cases?|complaints?)\s+(?:registered|filed|lodged)", "cases_filed"),
    (r"(?:aged?|ages?)\s+(\d+)\s*(?:to|-)\s*(\d+)", "age_range"),
]


class BrookingsBrideScraper(BasePDFReportScraper):
    """Scraper for the Brookings report on Pakistani brides trafficked to China.

    This is a one-time scraper targeting a specific research article
    and any associated PDFs from Brookings. It extracts statistical
    data points, key findings, and report metadata for the
    ``statistical_reports`` table.

    Attributes:
        name: Scraper identifier.
        source_url: Brookings article URL.
        schedule: One-time manual trigger.
        priority: P2 research reference.
    """

    name: str = "brookings_bride"
    source_url: str = "https://www.brookings.edu/articles/pakistani-brides/"
    schedule: str = "one-time"
    priority: str = "P2"

    rate_limit_delay: float = 2.0
    pdf_link_pattern: str = r"\.pdf"

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch the Brookings article and any linked PDFs.

        Strategy:
            1. Fetch the article HTML page.
            2. Extract inline statistics from the article text.
            3. Discover and download any linked PDF reports.
            4. Extract tables and text from PDFs.
            5. Combine all findings into statistical_reports records.

        Returns:
            List of statistical_reports records.
        """
        logger.info("[%s] Fetching Brookings article: %s", self.name, self.source_url)

        response = await self.fetch(self.source_url)
        html = response.text
        records = self._extract_article_stats(html)

        # Attempt to find and process linked PDFs
        pdf_urls = self.discover_pdf_urls(html)
        for pdf_url in pdf_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)
                pdf_records = self._process_pdf(pdf_path, pdf_url)
                records.extend(pdf_records)
            except Exception as exc:
                logger.error(
                    "[%s] Failed to process PDF %s: %s",
                    self.name, pdf_url, exc,
                )

        # If no PDFs found, still extract text-based stats from article
        if not pdf_urls:
            logger.info(
                "[%s] No PDFs found; relying on article text extraction",
                self.name,
            )

        logger.info("[%s] Extracted %d records", self.name, len(records))
        return records

    def _extract_article_stats(self, html: str) -> list[dict[str, Any]]:
        """Extract key statistics from the Brookings article HTML.

        Args:
            html: Raw HTML content of the article page.

        Returns:
            List of statistical_reports records extracted from the text.
        """
        soup = BeautifulSoup(html, "html.parser")
        scraped_at = datetime.now(timezone.utc).isoformat()

        # Extract article metadata
        title = ""
        title_tag = soup.find("h1")
        if title_tag:
            title = title_tag.get_text(strip=True)

        author = ""
        author_tag = soup.find("a", class_=re.compile(r"author", re.IGNORECASE))
        if author_tag:
            author = author_tag.get_text(strip=True)

        published_date = ""
        time_tag = soup.find("time")
        if time_tag:
            published_date = time_tag.get("datetime", time_tag.get_text(strip=True))

        # Get article body text
        body_text = ""
        article_body = soup.find("div", class_=re.compile(r"post-body|article-body|entry-content"))
        if article_body:
            body_text = article_body.get_text(separator=" ", strip=True)
        else:
            # Fallback: concatenate all paragraph text
            paragraphs = soup.find_all("p")
            body_text = " ".join(p.get_text(strip=True) for p in paragraphs)

        records: list[dict[str, Any]] = []

        # Always create a base record for the report itself
        base_record = {
            "source_name": "Brookings Institution",
            "report_title": title or "Pakistani Brides Sold to Chinese Men",
            "indicator": "cross_border_bride_trafficking",
            "value": 629,
            "unit": "victims",
            "year": published_date[:4] if published_date else "",
            "country": "Pakistan",
            "destination_country": "China",
            "author": author,
            "published_date": published_date,
            "source_url": self.source_url,
            "scraped_at": scraped_at,
        }
        records.append(base_record)

        # Extract additional statistics from the body text
        for pattern, indicator in _STAT_PATTERNS:
            matches = re.finditer(pattern, body_text, re.IGNORECASE)
            for match in matches:
                value_str = match.group(1).replace(",", "")
                try:
                    value = int(value_str)
                except ValueError:
                    continue

                stat_record = {
                    "source_name": "Brookings Institution",
                    "report_title": title or "Pakistani Brides Sold to Chinese Men",
                    "indicator": indicator,
                    "value": value,
                    "unit": "count",
                    "country": "Pakistan",
                    "source_url": self.source_url,
                    "scraped_at": scraped_at,
                    "context": match.group(0)[:200],
                }

                if indicator == "year_range":
                    stat_record["year_start"] = match.group(1)
                    stat_record["year_end"] = match.group(2)
                elif indicator == "age_range":
                    stat_record["age_min"] = match.group(1)
                    stat_record["age_max"] = match.group(2)

                records.append(stat_record)

        return records

    def _process_pdf(
        self, pdf_path: Path, pdf_url: str
    ) -> list[dict[str, Any]]:
        """Extract structured data from a downloaded PDF.

        Args:
            pdf_path: Path to the downloaded PDF file.
            pdf_url: Original URL of the PDF for provenance.

        Returns:
            List of statistical_reports records.
        """
        scraped_at = datetime.now(timezone.utc).isoformat()

        # Extract text
        full_text = self.extract_text(pdf_path)
        if not full_text:
            logger.warning("[%s] No text extracted from %s", self.name, pdf_path)
            return []

        # Extract tables
        tables = self.extract_tables(pdf_path)
        records = self.parse_tables(tables, pdf_url)

        # Also scan full text for statistics
        for pattern, indicator in _STAT_PATTERNS:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                value_str = match.group(1).replace(",", "")
                try:
                    value = int(value_str)
                except ValueError:
                    continue

                records.append({
                    "source_name": "Brookings Institution",
                    "report_title": "Pakistani Brides Report (PDF)",
                    "indicator": indicator,
                    "value": value,
                    "unit": "count",
                    "country": "Pakistan",
                    "source_url": pdf_url,
                    "scraped_at": scraped_at,
                    "context": match.group(0)[:200],
                })

        return records

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Convert PDF tables to statistical_reports records.

        Args:
            tables: Raw tables extracted from the PDF.
            pdf_url: Source URL for provenance.

        Returns:
            List of normalized records.
        """
        scraped_at = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []

        for table in tables:
            if len(table) < 2:
                continue

            header = [cell.strip().lower() for cell in table[0]]
            for row in table[1:]:
                if len(row) != len(header):
                    continue

                row_dict = dict(zip(header, row))
                record = {
                    "source_name": "Brookings Institution",
                    "report_title": "Pakistani Brides Report (PDF Table)",
                    "indicator": row_dict.get("indicator", row_dict.get("category", "")),
                    "value": row_dict.get("value", row_dict.get("count", row_dict.get("number", ""))),
                    "unit": row_dict.get("unit", "count"),
                    "country": "Pakistan",
                    "source_url": pdf_url,
                    "scraped_at": scraped_at,
                }
                # Only include rows with meaningful data
                if record["indicator"] or record["value"]:
                    records.append(record)

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Brookings statistical_reports record.

        Requires source_name, and at least indicator or report_title.

        Args:
            record: A single record dictionary.

        Returns:
            True if the record passes validation.
        """
        if not record.get("source_name"):
            return False
        if not (record.get("indicator") or record.get("report_title")):
            return False
        return True
