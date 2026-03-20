"""Tests for the ECPAT International Pakistan country assessment scraper."""

import pytest
import respx

from data.scrapers.international.ecpat import ECPATScraper


SAMPLE_ECPAT_HTML = """<html><body>
<h1>ECPAT Country Overview: Pakistan</h1>
<p>According to recent data, 22.8% children in Pakistan are affected by
child sexual exploitation.</p>
<div class="stat-block">
  <span>3,500 cases of child trafficking reported in 2023.</span>
</div>
<ul>
  <li><a href="https://ecpat.org/wp-content/uploads/pakistan-assessment-2023.pdf">
    Pakistan Country Assessment 2023</a></li>
  <li><a href="https://ecpat.org/wp-content/uploads/gbi-survey-2022.pdf">
    GBI Survey Report 2022</a></li>
</ul>
</body></html>"""


class TestECPATScraper:
    def test_init(self):
        scraper = ECPATScraper()
        assert scraper.name == "ecpat"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = ECPATScraper()
        record = {
            "source_name": "ecpat",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_with_report_title_only(self):
        scraper = ECPATScraper()
        record = {
            "source_name": "ecpat",
            "report_title": "ECPAT Assessment",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = ECPATScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_source_name(self):
        scraper = ECPATScraper()
        assert scraper.validate({"indicator": "test"}) is False

    def test_classify_indicator(self):
        scraper = ECPATScraper()
        assert scraper._classify_indicator("online exploitation") == (
            "online_child_sexual_exploitation"
        )
        assert scraper._classify_indicator("trafficking in children") == (
            "child_trafficking_sexual_exploitation"
        )

    def test_extract_value(self):
        scraper = ECPATScraper()
        assert scraper._extract_value(["Indicator", "123"]) == 123
        assert scraper._extract_value(["Indicator", "45.6"]) == 45.6
        assert scraper._extract_value(["No numbers here"]) is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get("https://ecpat.org/country/pakistan/").respond(
            200, text=SAMPLE_ECPAT_HTML
        )
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = ECPATScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
