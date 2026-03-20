"""Tests for BasePDFReportScraper."""

from pathlib import Path
from typing import Any

import pytest

from data.scrapers.base_pdf_scraper import BasePDFReportScraper


class MockPDFScraper(BasePDFReportScraper):
    """Concrete implementation for testing."""

    name = "mock_pdf"
    source_url = "https://example.com/reports"
    schedule = "0 0 1 1 *"
    priority = "P2"
    catalog_url = "https://example.com/reports"
    pdf_link_pattern = r"\.pdf$"

    def parse_tables(self, tables, pdf_url):
        records = []
        for table in tables:
            for row in table[1:]:  # skip header
                records.append({
                    "source_name": self.name,
                    "indicator": row[0] if row else "",
                    "value": float(row[1]) if len(row) > 1 and row[1] else 0,
                    "pdf_url": pdf_url,
                })
        return records


class TestBasePDFReportScraper:
    def test_discover_pdf_urls_absolute(self):
        scraper = MockPDFScraper()
        html = '<html><body><a href="https://example.com/report.pdf">Report</a></body></html>'
        urls = scraper.discover_pdf_urls(html)
        assert urls == ["https://example.com/report.pdf"]

    def test_discover_pdf_urls_relative(self):
        scraper = MockPDFScraper()
        html = '<html><body><a href="/files/report.pdf">Report</a></body></html>'
        urls = scraper.discover_pdf_urls(html)
        assert len(urls) == 1
        assert "report.pdf" in urls[0]

    def test_discover_pdf_urls_no_pdfs(self):
        scraper = MockPDFScraper()
        html = '<html><body><a href="/page.html">Page</a></body></html>'
        urls = scraper.discover_pdf_urls(html)
        assert urls == []

    def test_discover_pdf_urls_custom_pattern(self):
        scraper = MockPDFScraper()
        scraper.pdf_link_pattern = r"report.*\.pdf"
        html = '<html><body><a href="https://x.com/report_2024.pdf">R1</a><a href="https://x.com/other.pdf">R2</a></body></html>'
        urls = scraper.discover_pdf_urls(html)
        assert len(urls) == 1
        assert "report_2024.pdf" in urls[0]

    def test_validate_valid_record(self):
        scraper = MockPDFScraper()
        record = {"source_name": "test", "indicator": "child_labor"}
        assert scraper.validate(record) is True

    def test_validate_empty_record(self):
        scraper = MockPDFScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_indicator(self):
        scraper = MockPDFScraper()
        record = {"source_name": "test"}
        assert scraper.validate(record) is False

    def test_parse_tables_default_returns_empty(self):
        # Base class parse_tables returns empty list
        base = MockPDFScraper()
        # Override parse_tables back to base behavior
        result = BasePDFReportScraper.parse_tables(base, [], "https://x.com/test.pdf")
        assert result == []

    @pytest.mark.asyncio
    async def test_download_pdf(self, mock_http, raw_data_dir, monkeypatch):
        monkeypatch.setattr("data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir)
        mock_http.get("https://example.com/test.pdf").respond(200, content=b"%PDF-1.0 test content")

        scraper = MockPDFScraper()
        scraper.rate_limit_delay = 0
        path = await scraper.download_pdf("https://example.com/test.pdf")
        assert path.exists()
        assert path.name == "test.pdf"
        assert path.read_bytes().startswith(b"%PDF")
        await scraper.close()
