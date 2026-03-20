"""Tests for the Pahchaan hospital-based child protection data scraper."""

import pytest
import respx

from data.scrapers.government.pahchaan import PahchaanScraper


SAMPLE_PAHCHAAN_HTML = """<html><body>
<h1>Pahchaan - Hospital Based Child Protection</h1>
<p>Pahchaan maintains records of child abuse cases reported through
hospital networks across Pakistan since 2012.</p>
<table>
  <tr><th>Category</th><th>Male</th><th>Female</th><th>Total</th></tr>
  <tr><td>Physical Abuse</td><td>145</td><td>98</td><td>243</td></tr>
  <tr><td>Sexual Abuse</td><td>67</td><td>89</td><td>156</td></tr>
  <tr><td>Neglect</td><td>34</td><td>41</td><td>75</td></tr>
</table>
<a href="https://pahchaan.info/reports/annual-report-2023.pdf">
  Annual Report 2023</a>
</body></html>"""


class TestPahchaanScraper:
    def test_init(self):
        scraper = PahchaanScraper()
        assert scraper.name == "pahchaan"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = PahchaanScraper()
        record = {
            "source_name": "pahchaan",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = PahchaanScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_indicator(self):
        scraper = PahchaanScraper()
        assert scraper.validate({"source_name": "pahchaan"}) is False

    def test_classify_indicator(self):
        scraper = PahchaanScraper()
        assert scraper._classify_indicator("Physical abuse cases") == "physical_abuse"
        assert scraper._classify_indicator("Sexual abuse reported") == "sexual_abuse"
        assert scraper._classify_indicator("Child trafficking") == "trafficking"
        assert scraper._classify_indicator("Hospital referrals") == "hospital_referrals"

    def test_extract_year_from_context(self):
        scraper = PahchaanScraper()
        assert scraper._extract_year_from_context(
            "https://pahchaan.info/reports/annual-2023.pdf"
        ) == 2023
        assert scraper._extract_year_from_context(
            "https://pahchaan.info/report.pdf"
        ) is None

    def test_parse_numeric(self):
        scraper = PahchaanScraper()
        assert scraper._parse_numeric("1,234") == 1234
        assert scraper._parse_numeric("45.6") == 45.6
        assert scraper._parse_numeric("") is None
        assert scraper._parse_numeric("abc") is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get("https://pahchaan.info").respond(
            200, text=SAMPLE_PAHCHAAN_HTML
        )
        # Mock sub-pages — return empty HTML (no PDFs)
        respx.get(url__regex=r"https://pahchaan\.info/.*").respond(
            200, text="<html><body>No reports here.</body></html>"
        )
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = PahchaanScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
