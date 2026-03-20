"""Tests for the DOL TVPRA scraper."""

import pytest
import respx

from data.scrapers.international.dol_tvpra import DOLTVPRAScraper


MOCK_TVPRA_HTML = """<html><body>
<h1>List of Goods Produced by Child Labor or Forced Labor</h1>
<p>Download the full list:</p>
<a href="/sites/dolgov/files/ILAB/ListofGoods.xlsx">Download Excel</a>
</body></html>"""


class TestDOLTVPRAScraper:
    def test_init(self):
        scraper = DOLTVPRAScraper()
        assert scraper.name == "dol_tvpra"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = DOLTVPRAScraper()
        record = {
            "source_name": "dol_tvpra",
            "indicator": "tvpra_listed_good:bricks",
            "report_year": 2024,
            "value": 1,
            "good_name": "bricks",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = DOLTVPRAScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_good_name(self):
        scraper = DOLTVPRAScraper()
        record = {
            "source_name": "dol_tvpra",
            "indicator": "tvpra_listed_good:",
            "good_name": "",
        }
        assert scraper.validate(record) is False

    def test_extract_year_from_row(self):
        row = {"country": "Pakistan", "year": "2023", "good": "Bricks"}
        assert DOLTVPRAScraper._extract_year_from_row(row) == "2023"

    def test_extract_year_from_row_no_year(self):
        row = {"country": "Pakistan", "good": "Bricks"}
        year = DOLTVPRAScraper._extract_year_from_row(row)
        # Falls back to current year
        assert len(year) == 4

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        tvpra_url = (
            "https://www.dol.gov/agencies/ilab/reports/child-labor/"
            "list-of-goods"
        )
        respx.get(tvpra_url).respond(200, text=MOCK_TVPRA_HTML)

        # Mock Excel download with minimal bytes (will fail to parse
        # as real Excel, but scraper should handle gracefully)
        respx.get(url__regex=r".*\.xlsx$").respond(
            200,
            content=b"PK\x03\x04fake-xlsx-content",
            headers={"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        )

        scraper = DOLTVPRAScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
