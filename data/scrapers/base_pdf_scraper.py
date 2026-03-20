"""Base PDF report scraper for Nigehbaan data pipeline.

Extends BaseScraper with PDF-specific capabilities: discovery,
download, table extraction (pdfplumber primary, tabula fallback),
and text extraction.
"""

from pathlib import Path
from typing import Any

import logging
import re

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BasePDFReportScraper(BaseScraper):
    """Base class for scrapers that extract data from PDF reports.

    Provides PDF discovery, download, table/text extraction, and
    a template scrape() workflow. Subclasses override extract-specific
    methods and provide their own normalization logic.
    """

    # Override in subclasses
    catalog_url: str = ""
    pdf_link_pattern: str = r"\.pdf$"

    def discover_pdf_urls(self, html: str) -> list[str]:
        """Find PDF download links on a catalog/listing page.

        Args:
            html: Raw HTML content of the catalog page.

        Returns:
            List of absolute PDF URLs found on the page.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if re.search(self.pdf_link_pattern, href, re.IGNORECASE):
                if href.startswith("http"):
                    urls.append(href)
                elif href.startswith("/"):
                    # Build absolute URL from source_url
                    from urllib.parse import urlparse

                    parsed = urlparse(self.source_url)
                    urls.append(f"{parsed.scheme}://{parsed.netloc}{href}")
                else:
                    base = self.source_url.rstrip("/")
                    urls.append(f"{base}/{href}")

        return urls

    async def download_pdf(self, url: str) -> Path:
        """Download a PDF and store it locally.

        Args:
            url: URL of the PDF to download.

        Returns:
            Path to the downloaded PDF file.
        """
        raw_dir = self.get_raw_dir()
        filename = url.split("/")[-1].split("?")[0]
        if not filename.endswith(".pdf"):
            filename = f"{self.name}_{self.run_id}.pdf"
        file_path = raw_dir / filename

        content = await self.fetch_bytes(url)
        file_path.write_bytes(content)
        logger.info("[%s] Downloaded PDF: %s (%d bytes)", self.name, file_path, len(content))
        return file_path

    def extract_tables(self, pdf_path: Path) -> list[list[list[str]]]:
        """Extract tables from a PDF using pdfplumber, with tabula fallback.

        Args:
            pdf_path: Path to the local PDF file.

        Returns:
            List of tables, each a list of rows (list of cell strings).
        """
        tables = self._extract_tables_pdfplumber(pdf_path)
        if not tables:
            tables = self._extract_tables_tabula(pdf_path)
        return tables

    def _extract_tables_pdfplumber(self, pdf_path: Path) -> list[list[list[str]]]:
        """Primary table extraction via pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed")
            return []

        tables: list[list[list[str]]] = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            cleaned = [
                                [cell or "" for cell in row]
                                for row in table
                                if row
                            ]
                            if cleaned and len(cleaned) > 1:
                                tables.append(cleaned)
        except Exception as exc:
            logger.warning("[%s] pdfplumber extraction failed: %s", self.name, exc)

        return tables

    def _extract_tables_tabula(self, pdf_path: Path) -> list[list[list[str]]]:
        """Fallback table extraction via tabula-py."""
        try:
            import tabula
        except ImportError:
            logger.warning("tabula-py not installed, skipping fallback")
            return []

        tables: list[list[list[str]]] = []
        try:
            dfs = tabula.read_pdf(str(pdf_path), pages="all", lattice=True)
            for df in dfs:
                header = [str(c) for c in df.columns.tolist()]
                rows = [[str(cell) if cell else "" for cell in row] for row in df.values.tolist()]
                tables.append([header] + rows)
        except Exception:
            try:
                dfs = tabula.read_pdf(str(pdf_path), pages="all", stream=True)
                for df in dfs:
                    header = [str(c) for c in df.columns.tolist()]
                    rows = [[str(cell) if cell else "" for cell in row] for row in df.values.tolist()]
                    tables.append([header] + rows)
            except Exception as exc:
                logger.warning("[%s] tabula fallback also failed: %s", self.name, exc)

        return tables

    def extract_text(self, pdf_path: Path, pages: list[int] | None = None) -> str:
        """Extract plain text from a PDF.

        Args:
            pdf_path: Path to the local PDF file.
            pages: Optional 0-indexed page numbers. None = all pages.

        Returns:
            Concatenated text from the requested pages.
        """
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed")
            return ""

        texts: list[str] = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                target = (
                    [pdf.pages[i] for i in pages if i < len(pdf.pages)]
                    if pages is not None
                    else pdf.pages
                )
                for page in target:
                    text = page.extract_text()
                    if text:
                        texts.append(text)
        except Exception as exc:
            logger.warning("[%s] Text extraction failed: %s", self.name, exc)

        return "\n\n".join(texts)

    async def scrape(self) -> list[dict[str, Any]]:
        """Template scrape workflow: fetch catalog -> find PDFs -> download -> extract -> normalize.

        Subclasses should override parse_tables() for source-specific normalization.
        """
        url = self.catalog_url or self.source_url
        response = await self.fetch(url)
        pdf_urls = self.discover_pdf_urls(response.text)

        if not pdf_urls:
            logger.warning("[%s] No PDF URLs found at %s", self.name, url)
            return []

        all_records: list[dict[str, Any]] = []
        for pdf_url in pdf_urls:
            try:
                pdf_path = await self.download_pdf(pdf_url)
                tables = self.extract_tables(pdf_path)
                records = self.parse_tables(tables, pdf_url)
                all_records.extend(records)
            except Exception as exc:
                logger.error("[%s] Failed to process %s: %s", self.name, pdf_url, exc)

        return all_records

    def parse_tables(
        self, tables: list[list[list[str]]], pdf_url: str
    ) -> list[dict[str, Any]]:
        """Convert extracted tables to structured records.

        Override in subclasses for source-specific parsing.

        Args:
            tables: Raw tables from PDF extraction.
            pdf_url: Source URL for provenance.

        Returns:
            List of normalized record dicts.
        """
        return []

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a statistical report record.

        Checks that source_name and at least indicator or report_title exist.
        """
        return bool(
            record.get("source_name")
            and (record.get("indicator") or record.get("report_title"))
        )
