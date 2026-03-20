"""Tests for the Bytes for All (B4A) digital rights scraper."""

import pytest
import respx

from data.scrapers.government.bytes_for_all import BytesForAllScraper


SAMPLE_B4A_HTML = """<html><body>
<h1>Bytes for All - Digital Rights Pakistan</h1>
<p>Bytes for All has documented 1,234 cases of online child exploitation
in Pakistan during 2024.</p>
<table>
  <tr><th>Category</th><th>Count</th></tr>
  <tr><td>Online Child Exploitation</td><td>1,234</td></tr>
  <tr><td>CSAM Reports Filed</td><td>567</td></tr>
  <tr><td>Cyber Harassment of Minors</td><td>890</td></tr>
  <tr><td>Digital Safety Trainings</td><td>45</td></tr>
</table>
<a href="https://bytesforall.pk/publications/annual-report-2024.pdf">
  Annual Report 2024</a>
</body></html>"""


class TestBytesForAllScraper:
    def test_init(self):
        scraper = BytesForAllScraper()
        assert scraper.name == "bytes_for_all"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = BytesForAllScraper()
        record = {
            "source_name": "bytes_for_all",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = BytesForAllScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_source(self):
        scraper = BytesForAllScraper()
        assert scraper.validate({"indicator": "test"}) is False

    def test_validate_missing_indicator(self):
        scraper = BytesForAllScraper()
        assert scraper.validate({"source_name": "bytes_for_all"}) is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get(url__regex=r".*bytesforall.*").respond(
            200, text=SAMPLE_B4A_HTML
        )
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = BytesForAllScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
