"""Tests for the Sahil 'Cruel Numbers' annual report scraper."""

import pytest
import respx

from data.scrapers.government.sahil import SahilScraper


SAMPLE_CATALOG_HTML = """<html><body>
<h1>Cruel Numbers Reports</h1>
<ul>
  <li><a href="https://sahil.org/wp-content/uploads/cruel-numbers-2023.pdf">
    Cruel Numbers 2023</a></li>
  <li><a href="https://sahil.org/wp-content/uploads/cruel-numbers-2022.pdf">
    Cruel Numbers 2022</a></li>
  <li><a href="/about">About Sahil</a></li>
</ul>
</body></html>"""


class TestSahilScraper:
    def test_init(self):
        scraper = SahilScraper()
        assert scraper.name == "sahil"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = SahilScraper()
        record = {
            "source_name": "sahil",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = SahilScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_indicator(self):
        scraper = SahilScraper()
        record = {"source_name": "sahil"}
        assert scraper.validate(record) is False

    def test_validate_missing_source_name(self):
        scraper = SahilScraper()
        record = {"indicator": "test"}
        assert scraper.validate(record) is False

    def test_extract_year_from_url(self):
        scraper = SahilScraper()
        assert scraper._extract_year_from_url(
            "https://sahil.org/cruel-numbers-2023.pdf"
        ) == 2023
        assert scraper._extract_year_from_url(
            "https://sahil.org/report.pdf"
        ) is None

    def test_discover_pdf_urls(self):
        scraper = SahilScraper()
        urls = scraper.discover_pdf_urls(SAMPLE_CATALOG_HTML)
        assert len(urls) == 2
        assert all(".pdf" in url for url in urls)

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get("https://sahil.org/cruel-numbers/").respond(
            200, text=SAMPLE_CATALOG_HTML
        )
        # Mock the PDF download — return minimal bytes
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = SahilScraper()
        scraper.rate_limit_delay = 0
        # scrape() will try to parse the fake PDF and likely get 0 records,
        # but should not crash
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
