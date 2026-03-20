"""Tests for the BLLF scraper."""

import pytest
import respx

from data.scrapers.government.bllf import BLLFScraper


MOCK_BLLF_HTML = """<html><body>
<h1>Bonded Labour Liberation Front</h1>
<p>Since inception, BLLF has freed 85,000+ bonded labourers across Pakistan.
Approximately 45% of them are children.</p>
<table>
  <thead>
    <tr><th>Province</th><th>Labourers Freed</th></tr>
  </thead>
  <tbody>
    <tr><td>Punjab</td><td>45,000</td></tr>
    <tr><td>Sindh</td><td>25,000</td></tr>
    <tr><td>KP</td><td>10,000</td></tr>
  </tbody>
</table>
</body></html>"""


class TestBLLFScraper:
    def test_init(self):
        scraper = BLLFScraper()
        assert scraper.name == "bllf"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = BLLFScraper()
        record = {
            "source_name": "bllf",
            "indicator": "bonded_labourers_freed",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = BLLFScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_indicator(self):
        scraper = BLLFScraper()
        record = {"source_name": "bllf"}
        assert scraper.validate(record) is False

    def test_build_indicator(self):
        row = {"category": "Freed Workers", "value": "1234"}
        indicator = BLLFScraper._build_indicator(row)
        assert indicator.startswith("bllf_")
        assert "freed" in indicator.lower()

    def test_extract_value(self):
        row = {"category": "Total", "count": "45,000"}
        value = BLLFScraper._extract_value(row)
        assert value == 45000.0

    def test_extract_value_no_numeric(self):
        row = {"category": "Label", "detail": "No numbers here"}
        value = BLLFScraper._extract_value(row)
        assert value is None

    def test_detect_gender(self):
        row = {"group": "Female workers", "count": "100"}
        assert BLLFScraper._detect_gender(row) == "female"

        row_male = {"group": "Male workers", "count": "200"}
        assert BLLFScraper._detect_gender(row_male) == "male"

    def test_deduplicate(self):
        records = [
            {"indicator": "freed", "geographic_scope": "Punjab"},
            {"indicator": "freed", "geographic_scope": "Punjab"},
            {"indicator": "freed", "geographic_scope": "Sindh"},
        ]
        unique = BLLFScraper._deduplicate(records)
        assert len(unique) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        respx.get(url__regex=r".*bllfpk\.com.*").respond(
            200, text=MOCK_BLLF_HTML
        )

        scraper = BLLFScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
