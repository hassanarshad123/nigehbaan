"""PDF text and table extraction wrapper using pdfplumber."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text and tables from PDF files.

    Uses ``pdfplumber`` for high-fidelity extraction of both flowing text
    and tabular data commonly found in NGO reports and court judgments.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"PDF not found: {self.path}")

    def extract_text(self, pages: list[int] | None = None) -> str:
        """Extract plain text from the PDF.

        Args:
            pages: Optional 0-indexed page numbers to extract.
                   If ``None``, all pages are extracted.

        Returns:
            Concatenated text from the requested pages.
        """
        texts: list[str] = []
        with pdfplumber.open(self.path) as pdf:
            target_pages = (
                [pdf.pages[i] for i in pages if i < len(pdf.pages)]
                if pages is not None
                else pdf.pages
            )
            for page in target_pages:
                page_text = page.extract_text()
                if page_text:
                    texts.append(page_text)

        result = "\n\n".join(texts)
        logger.info(
            "Extracted %d characters from %d pages of %s",
            len(result),
            len(texts),
            self.path.name,
        )
        return result

    def extract_tables(self, pages: list[int] | None = None) -> list[list[list[str | None]]]:
        """Extract tables from the PDF.

        Args:
            pages: Optional 0-indexed page numbers to extract tables from.

        Returns:
            A list of tables, where each table is a list of rows,
            and each row is a list of cell values (strings or None).
        """
        all_tables: list[list[list[str | None]]] = []
        with pdfplumber.open(self.path) as pdf:
            target_pages = (
                [pdf.pages[i] for i in pages if i < len(pdf.pages)]
                if pages is not None
                else pdf.pages
            )
            for page in target_pages:
                page_tables = page.extract_tables()
                if page_tables:
                    all_tables.extend(page_tables)

        logger.info(
            "Extracted %d tables from %s",
            len(all_tables),
            self.path.name,
        )
        return all_tables

    @property
    def page_count(self) -> int:
        """Return the total number of pages in the PDF."""
        with pdfplumber.open(self.path) as pdf:
            return len(pdf.pages)

    def extract_metadata(self) -> dict[str, Any]:
        """Return PDF metadata (author, title, creation date, etc.)."""
        with pdfplumber.open(self.path) as pdf:
            return dict(pdf.metadata) if pdf.metadata else {}
