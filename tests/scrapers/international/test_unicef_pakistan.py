"""Tests for the UNICEF Pakistan child protection data scraper."""

import pytest
import respx

from data.scrapers.international.unicef_pakistan import UNICEFPakistanScraper


SAMPLE_UNICEF_HTML = """<html><body>
<h1>UNICEF Pakistan - Child Protection</h1>
<div class="stat-block">
  <p>42% of children in Pakistan have their births registered.</p>
</div>
<div class="stat-block">
  <p>An estimated 12 million children are engaged in child labour.</p>
</div>
<table>
  <tr><th>Indicator</th><th>Value</th><th>Year</th></tr>
  <tr><td>Birth Registration</td><td>42%</td><td>2023</td></tr>
  <tr><td>Child Marriage (before 18)</td><td>18.3%</td><td>2023</td></tr>
  <tr><td>Child Labour</td><td>11.5%</td><td>2022</td></tr>
</table>
<a href="https://www.unicef.org/pakistan/media/report-2023.pdf">
  Annual Report 2023</a>
</body></html>"""


class TestUNICEFPakistanScraper:
    def test_init(self):
        scraper = UNICEFPakistanScraper()
        assert scraper.name == "unicef_pakistan"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = UNICEFPakistanScraper()
        record = {
            "source_name": "unicef_pakistan",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_with_report_title_only(self):
        scraper = UNICEFPakistanScraper()
        record = {
            "source_name": "unicef_pakistan",
            "report_title": "UNICEF Report",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = UNICEFPakistanScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_source(self):
        scraper = UNICEFPakistanScraper()
        assert scraper.validate({"indicator": "test"}) is False

    def test_classify_indicator(self):
        scraper = UNICEFPakistanScraper()
        assert scraper._classify_indicator("Birth registration rate") == "birth_registration"
        assert scraper._classify_indicator("Child labour prevalence") == "child_labor"
        assert scraper._classify_indicator("Child marriage before 18") == "child_marriage"
        assert scraper._classify_indicator("Trafficking cases") == "child_trafficking"

    def test_parse_value(self):
        scraper = UNICEFPakistanScraper()
        assert scraper._parse_value("42%") == 42
        assert scraper._parse_value("1,234") == 1234
        assert scraper._parse_value("18.3") == 18.3
        assert scraper._parse_value("") is None
        assert scraper._parse_value("N/A") is None

    def test_extract_year(self):
        scraper = UNICEFPakistanScraper()
        assert scraper._extract_year("Report for 2023") == 2023
        assert scraper._extract_year("No year here") is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        # Mock all UNICEF pages
        respx.get(url__regex=r".*unicef\.org.*").respond(
            200, text=SAMPLE_UNICEF_HTML
        )
        respx.get(url__regex=r".*data\.unicef\.org.*").respond(
            200, text=SAMPLE_UNICEF_HTML
        )
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = UNICEFPakistanScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
