"""Tests for the NCRC (National Commission on the Rights of the Child) scraper."""

import pytest
import respx

from data.scrapers.government.ncrc import NCRCScraper


SAMPLE_NCRC_HTML = """<html><body>
<h1>National Commission on the Rights of the Child</h1>
<p>NCRC is mandated to monitor child rights implementation in Pakistan.</p>
<table>
  <tr><th>Indicator</th><th>Province</th><th>Cases 2023</th></tr>
  <tr><td>Child Labour</td><td>Punjab</td><td>12,345</td></tr>
  <tr><td>Child Marriage</td><td>Sindh</td><td>3,456</td></tr>
  <tr><td>Street Children</td><td>KP</td><td>1,890</td></tr>
</table>
<a href="https://ncrc.gov.pk/uploads/state-of-children-2024.pdf">
  State of Children Report 2024</a>
<a href="https://ncrc.gov.pk/uploads/street-children-policy-2023.pdf">
  Street Children Policy 2023</a>
</body></html>"""


class TestNCRCScraper:
    def test_init(self):
        scraper = NCRCScraper()
        assert scraper.name == "ncrc"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = NCRCScraper()
        record = {
            "source_name": "ncrc",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_with_report_title_only(self):
        scraper = NCRCScraper()
        record = {
            "source_name": "ncrc",
            "report_title": "State of Children 2024",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = NCRCScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_source(self):
        scraper = NCRCScraper()
        assert scraper.validate({"indicator": "test"}) is False

    def test_classify_indicator(self):
        scraper = NCRCScraper()
        assert scraper._classify_indicator("Child labour cases") == "child_labor"
        assert scraper._classify_indicator("Street children count") == "street_children"
        assert scraper._classify_indicator("Child marriage") == "child_marriage"
        assert scraper._classify_indicator("Trafficking detected") == "child_trafficking"
        assert scraper._classify_indicator("Sexual abuse reported") == "child_sexual_abuse"

    def test_detect_province(self):
        scraper = NCRCScraper()
        headers = ["indicator", "province", "count"]
        row = ["Child Labour", "Punjab", "123"]
        assert scraper._detect_province(row, headers) == "Punjab"

        row_kp = ["Street Children", "KP", "456"]
        assert scraper._detect_province(row_kp, headers) == "Khyber Pakhtunkhwa"

    def test_parse_numeric(self):
        scraper = NCRCScraper()
        assert scraper._parse_numeric("12,345") == 12345
        assert scraper._parse_numeric("45.6%") == 45.6
        assert scraper._parse_numeric("") is None
        assert scraper._parse_numeric("N/A") is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get("https://ncrc.gov.pk").respond(200, text=SAMPLE_NCRC_HTML)
        # Mock sub-pages
        respx.get(url__regex=r"https://ncrc\.gov\.pk/.*").respond(
            200, text="<html><body>No additional data.</body></html>"
        )
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = NCRCScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
