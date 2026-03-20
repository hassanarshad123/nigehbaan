"""Tests for the DRF (Digital Rights Foundation) Cyber Harassment Helpline scraper."""

import pytest
import respx

from data.scrapers.government.drf_newsletters import DRFNewslettersScraper


SAMPLE_DRF_HTML = """<html><body>
<h1>DRF Cyber Harassment Helpline</h1>
<p>Since its launch, the helpline has received 18,500 total complaints
with a monthly average of 263 complaints per month. Approximately
70% female complainants have reported online harassment.</p>
<table>
  <tr><th>Category</th><th>Count</th></tr>
  <tr><td>Online Harassment</td><td>5,678</td></tr>
  <tr><td>Sextortion</td><td>2,345</td></tr>
  <tr><td>Image-Based Abuse</td><td>1,890</td></tr>
  <tr><td>Cyberbullying</td><td>3,456</td></tr>
  <tr><td>Stalking</td><td>1,234</td></tr>
</table>
<a href="https://digitalrightsfoundation.pk/newsletter-2024/">
  Helpline Newsletter 2024</a>
<a href="https://digitalrightsfoundation.pk/annual-report-2023/">
  Annual Report 2023</a>
</body></html>"""


class TestDRFNewslettersScraper:
    def test_init(self):
        scraper = DRFNewslettersScraper()
        assert scraper.name == "drf_newsletters"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = DRFNewslettersScraper()
        record = {
            "source_name": "Digital Rights Foundation",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
            "geographic_scope": "Pakistan",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = DRFNewslettersScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_source(self):
        scraper = DRFNewslettersScraper()
        record = {"indicator": "test", "geographic_scope": "Pakistan"}
        assert scraper.validate(record) is False

    def test_validate_missing_indicator(self):
        scraper = DRFNewslettersScraper()
        record = {
            "source_name": "Digital Rights Foundation",
            "geographic_scope": "Pakistan",
        }
        assert scraper.validate(record) is False

    def test_validate_missing_geographic_scope(self):
        scraper = DRFNewslettersScraper()
        record = {
            "source_name": "Digital Rights Foundation",
            "indicator": "test",
        }
        assert scraper.validate(record) is False

    def test_parse_numeric(self):
        scraper = DRFNewslettersScraper()
        assert scraper._parse_numeric("18,500") == 18500.0
        assert scraper._parse_numeric("70%") == 70.0
        assert scraper._parse_numeric("263") == 263.0
        assert scraper._parse_numeric("") is None

    def test_extract_year(self):
        scraper = DRFNewslettersScraper()
        assert scraper._extract_year("Annual Report 2023") == 2023
        assert scraper._extract_year("No year here") is None

    def test_is_relevant_category(self):
        scraper = DRFNewslettersScraper()
        assert scraper._is_relevant_category("sextortion cases") is True
        assert scraper._is_relevant_category("child exploitation") is True
        assert scraper._is_relevant_category("cyberbullying") is True
        assert scraper._is_relevant_category("weather report") is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get(url__regex=r".*digitalrightsfoundation\.pk.*").respond(
            200, text=SAMPLE_DRF_HTML
        )
        scraper = DRFNewslettersScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
