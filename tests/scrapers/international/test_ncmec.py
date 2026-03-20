"""Tests for the NCMEC (National Center for Missing & Exploited Children) scraper."""

import pytest
import respx

from data.scrapers.international.ncmec import NCMECScraper


SAMPLE_NCMEC_HTML = """<html><body>
<h1>NCMEC Data & Reports</h1>
<p>The CyberTipline received over 36 million reports in 2023.</p>
<ul>
  <li><a href="https://www.missingkids.org/content/dam/report-2023-data.pdf">
    2023 Annual Data Report</a></li>
  <li><a href="https://www.missingkids.org/content/dam/report-2022-data.pdf">
    2022 Annual Data Report</a></li>
</ul>
<table>
  <tr><th>Country</th><th>CyberTipline Reports</th><th>Year</th></tr>
  <tr><td>Pakistan</td><td>1,800,000</td><td>2023</td></tr>
  <tr><td>India</td><td>5,200,000</td><td>2023</td></tr>
</table>
</body></html>"""


class TestNCMECScraper:
    def test_init(self):
        scraper = NCMECScraper()
        assert scraper.name == "ncmec"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = NCMECScraper()
        record = {
            "source_name": "ncmec",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
            "pdf_url": "https://example.com/report.pdf",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = NCMECScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_pdf_url(self):
        scraper = NCMECScraper()
        record = {"source_name": "ncmec", "indicator": "test"}
        assert scraper.validate(record) is False

    def test_validate_missing_indicator(self):
        scraper = NCMECScraper()
        record = {
            "source_name": "ncmec",
            "pdf_url": "https://example.com/report.pdf",
        }
        assert scraper.validate(record) is False

    def test_extract_year_from_url(self):
        scraper = NCMECScraper()
        assert scraper._extract_year_from_url(
            "https://example.com/report-2023-data.pdf"
        ) == 2023
        assert scraper._extract_year_from_url(
            "https://example.com/report.pdf"
        ) is None

    def test_parse_numeric(self):
        scraper = NCMECScraper()
        assert scraper._parse_numeric("1,800,000") == 1800000.0
        assert scraper._parse_numeric("45.6") == 45.6
        assert scraper._parse_numeric("") is None

    def test_row_mentions_pakistan(self):
        scraper = NCMECScraper()
        assert scraper._row_mentions_pakistan(["Pakistan", "1,800,000"]) is True
        assert scraper._row_mentions_pakistan(["India", "5,200,000"]) is False

    def test_row_is_relevant(self):
        scraper = NCMECScraper()
        assert scraper._row_is_relevant(["CyberTipline Reports", "36,000,000"]) is True
        assert scraper._row_is_relevant(["Weather Data", "100"]) is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get(url__regex=r".*missingkids\.org.*").respond(
            200, text=SAMPLE_NCMEC_HTML
        )
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = NCMECScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
