"""Tests for the ILOSTAT API scraper."""

import pytest
import respx

from data.scrapers.international.ilostat_api import ILOSTATAPIScraper


class TestILOSTATAPIScraper:
    def test_init(self):
        scraper = ILOSTATAPIScraper()
        assert scraper.name == "ilostat_api"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = ILOSTATAPIScraper()
        record = {
            "source_name": "ilostat_api",
            "indicator": "child_labor_rate_sdg_8_7_1",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = ILOSTATAPIScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_indicator(self):
        scraper = ILOSTATAPIScraper()
        record = {"source_name": "ilostat_api", "report_year": 2024, "value": 10.0}
        assert scraper.validate(record) is False

    def test_validate_missing_value(self):
        scraper = ILOSTATAPIScraper()
        record = {
            "source_name": "ilostat_api",
            "indicator": "test",
            "report_year": 2024,
        }
        assert scraper.validate(record) is False

    def test_to_record_valid(self):
        row = {
            "ref_area": "PAK",
            "sex": "SEX_T",
            "classif1": "AGE_Y5-17",
            "time": "2019",
            "obs_value": "11.5",
        }
        record = ILOSTATAPIScraper._to_record(row)
        assert record is not None
        assert record["source_name"] == "ilostat_api"
        assert record["value"] == 11.5
        assert record["victim_gender"] == "total"
        assert record["victim_age_bracket"] == "5-17"

    def test_to_record_empty_obs_value(self):
        row = {"ref_area": "PAK", "obs_value": ""}
        record = ILOSTATAPIScraper._to_record(row)
        assert record is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, sample_csv_content, raw_data_dir, monkeypatch):
        import gzip

        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        compressed = gzip.compress(sample_csv_content.encode("utf-8"))
        respx.get(url__regex=r".*ilostat.*\.csv\.gz").respond(
            200, content=compressed
        )

        scraper = ILOSTATAPIScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
