"""Tests for the WeProtect Global Threat Assessment scraper."""

import pytest
import respx

from data.scrapers.international.weprotect_gta import WeProtectGTAScraper


SAMPLE_WEPROTECT_HTML = """<html><body>
<h1>Global Threat Assessment 2023</h1>
<p>The WeProtect Global Alliance's Global Threat Assessment examines
the scale and nature of online child sexual exploitation and abuse.</p>
<ul>
  <li><a href="https://www.weprotect.org/media/gta-2023.pdf">
    Download the Global Threat Assessment 2023 (PDF)</a></li>
  <li><a href="https://www.weprotect.org/media/threat-assessment-2021.pdf">
    Global Threat Assessment 2021</a></li>
</ul>
<p>In 2023, NCMEC received over 36 million CyberTipline reports.
Self-generated CSAM accounted for 92% of imagery.</p>
</body></html>"""


class TestWeProtectGTAScraper:
    def test_init(self):
        scraper = WeProtectGTAScraper()
        assert scraper.name == "weprotect_gta"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = WeProtectGTAScraper()
        record = {
            "source_name": "WeProtect Global Alliance",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_with_report_title(self):
        scraper = WeProtectGTAScraper()
        record = {
            "source_name": "WeProtect Global Alliance",
            "indicator": "CSAM Reports to NCMEC",
            "report_title": "Global Threat Assessment",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = WeProtectGTAScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_source(self):
        scraper = WeProtectGTAScraper()
        assert scraper.validate({"indicator": "test"}) is False

    def test_validate_missing_indicator(self):
        scraper = WeProtectGTAScraper()
        assert scraper.validate({"source_name": "WeProtect"}) is False

    def test_extract_year(self):
        scraper = WeProtectGTAScraper()
        assert scraper._extract_year(
            "https://www.weprotect.org/media/gta-2023.pdf"
        ) == 2023
        assert scraper._extract_year("no year") is None

    def test_parse_numeric(self):
        scraper = WeProtectGTAScraper()
        assert scraper._parse_numeric("36,000,000") == 36000000.0
        assert scraper._parse_numeric("92%") == 92.0
        assert scraper._parse_numeric("") is None

    def test_parse_numeric_with_magnitude(self):
        scraper = WeProtectGTAScraper()
        assert scraper._parse_numeric("36 million reports") == 36_000_000.0
        assert scraper._parse_numeric("2.5 billion items") == 2_500_000_000.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get(url__regex=r".*weprotect\.org.*").respond(
            200, text=SAMPLE_WEPROTECT_HTML
        )
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = WeProtectGTAScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
