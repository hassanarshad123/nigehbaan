"""Tests for the Google Transparency Report scraper."""

import pytest
import respx

from data.scrapers.international.google_transparency import GoogleTransparencyScraper


SAMPLE_GOOGLE_PK_HTML = """<html><body>
<h1>Government Requests to Remove Content - Pakistan</h1>
<p>H1 2024</p>
<table>
  <tr><th>Product</th><th>Requests</th><th>Items Requested</th><th>Items Removed</th></tr>
  <tr><td>YouTube</td><td>245</td><td>1,892</td><td>1,456</td></tr>
  <tr><td>Google Search</td><td>89</td><td>567</td><td>234</td></tr>
</table>
</body></html>"""

SAMPLE_GOOGLE_CSAM_HTML = """<html><body>
<h2>Child Sexual Abuse Material</h2>
<p>H2 2024</p>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>CSAM - Hashes Identified</td><td>3,400,000</td></tr>
  <tr><td>CSAM - URLs Removed</td><td>1,200,000</td></tr>
</table>
</body></html>"""

SAMPLE_GOOGLE_OVERVIEW_HTML = """<html><body>
<h1>Google Transparency Report</h1>
<p>H1 2024</p>
<table>
  <tr><th>Category</th><th>Total Requests</th></tr>
  <tr><td>Child sexual exploitation content</td><td>890,000</td></tr>
  <tr><td>Copyright</td><td>45,000,000</td></tr>
</table>
</body></html>"""


class TestGoogleTransparencyScraper:
    def test_init(self):
        scraper = GoogleTransparencyScraper()
        assert scraper.name == "google_transparency"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = GoogleTransparencyScraper()
        record = {
            "platform": "Google",
            "metric": "test_metric",
            "report_period": "H1 2025",
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = GoogleTransparencyScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_platform(self):
        scraper = GoogleTransparencyScraper()
        record = {"metric": "test", "value": 100.0}
        assert scraper.validate(record) is False

    def test_validate_missing_metric(self):
        scraper = GoogleTransparencyScraper()
        record = {"platform": "Google", "value": 100.0}
        assert scraper.validate(record) is False

    def test_validate_none_value(self):
        scraper = GoogleTransparencyScraper()
        record = {"platform": "Google", "metric": "test", "value": None}
        assert scraper.validate(record) is False

    def test_parse_numeric(self):
        scraper = GoogleTransparencyScraper()
        assert scraper._parse_numeric("3,400,000") == 3400000.0
        assert scraper._parse_numeric("14.4M") == 14_400_000.0
        assert scraper._parse_numeric("99.6%") == 99.6
        assert scraper._parse_numeric("450K") == 450_000.0
        assert scraper._parse_numeric("") is None

    def test_extract_period(self):
        scraper = GoogleTransparencyScraper()
        assert scraper._extract_period("H1 2024") == "H1 2024"
        assert scraper._extract_period("H2 2023") == "H2 2023"
        assert scraper._extract_period(
            "Jan 2024 - Jun 2024"
        ) == "Jan 2024 - Jun 2024"

    def test_is_child_safety_related(self):
        scraper = GoogleTransparencyScraper()
        assert scraper._is_child_safety_related(
            "Child sexual exploitation content"
        ) is True
        assert scraper._is_child_safety_related("CSAM removal") is True
        assert scraper._is_child_safety_related("Copyright claims") is False

    def test_infer_unit(self):
        scraper = GoogleTransparencyScraper()
        assert scraper._infer_unit("Removal Requests", "245") == "requests"
        assert scraper._infer_unit("Compliance Rate", "95%") == "percent"
        assert scraper._infer_unit("Items Removed", "1456") == "items"

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get(url__regex=r".*government-removals/by-country/PK.*").respond(
            200, text=SAMPLE_GOOGLE_PK_HTML
        )
        respx.get(url__regex=r".*child-sexual-abuse-material.*").respond(
            200, text=SAMPLE_GOOGLE_CSAM_HTML
        )
        respx.get(url__regex=r".*government-removals/overview.*").respond(
            200, text=SAMPLE_GOOGLE_OVERVIEW_HTML
        )
        scraper = GoogleTransparencyScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
