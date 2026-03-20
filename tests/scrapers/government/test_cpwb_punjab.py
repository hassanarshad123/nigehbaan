"""Tests for the CPWB Punjab (Child Protection & Welfare Bureau) scraper."""

import pytest
import respx

from data.scrapers.government.cpwb_punjab import CPWBPunjabScraper


SAMPLE_CPWB_HTML = """<html><body>
<h1>Child Protection & Welfare Bureau Punjab</h1>
<div class="stat-counter">
  <span>15,234</span> Children Rescued
</div>
<div class="stat-counter">
  <span>8,500</span> Helpline 1121 Calls
</div>
<table>
  <tr><th>Category</th><th>Total</th></tr>
  <tr><td>Children Rescued</td><td>15,234</td></tr>
  <tr><td>Helpline 1121 Calls</td><td>42,567</td></tr>
  <tr><td>FIR Registered</td><td>3,890</td></tr>
  <tr><td>Sexual Abuse Cases</td><td>1,234</td></tr>
  <tr><td>Children Reunited with Families</td><td>12,456</td></tr>
</table>
</body></html>"""


class TestCPWBPunjabScraper:
    def test_init(self):
        scraper = CPWBPunjabScraper()
        assert scraper.name == "cpwb_punjab"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = CPWBPunjabScraper()
        record = {
            "source_name": "cpwb_punjab",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = CPWBPunjabScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_indicator(self):
        scraper = CPWBPunjabScraper()
        assert scraper.validate({"source_name": "cpwb_punjab"}) is False

    def test_validate_missing_source(self):
        scraper = CPWBPunjabScraper()
        assert scraper.validate({"indicator": "test"}) is False

    def test_classify_indicator(self):
        scraper = CPWBPunjabScraper()
        assert scraper._classify_indicator("Helpline 1121 Calls") == "helpline_1121_calls"
        assert scraper._classify_indicator("Children Rescued") == "children_rescued"
        assert scraper._classify_indicator("FIR Registered") == "fir_registered"
        assert scraper._classify_indicator("Sexual Abuse Cases") == "sexual_abuse_cases"
        assert scraper._classify_indicator("Children Reunited") == "children_reunited"

    def test_parse_numeric(self):
        scraper = CPWBPunjabScraper()
        assert scraper._parse_numeric("15,234") == 15234
        assert scraper._parse_numeric("5000+") == 5000
        assert scraper._parse_numeric("45.6") == 45.6
        assert scraper._parse_numeric("") is None
        assert scraper._parse_numeric("N/A") is None

    def test_extract_year(self):
        scraper = CPWBPunjabScraper()
        assert scraper._extract_year("Statistics for 2024") == 2024
        assert scraper._extract_year("No year") is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        # Mock all CPWB pages
        respx.get(url__regex=r".*cpwb\.punjab\.gov\.pk.*").respond(
            200, text=SAMPLE_CPWB_HTML
        )
        scraper = CPWBPunjabScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
