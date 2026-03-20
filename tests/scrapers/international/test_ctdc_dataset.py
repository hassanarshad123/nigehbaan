"""Tests for the CTDC Dataset scraper."""

import pytest

from data.scrapers.international.ctdc_dataset import CTDCDatasetScraper


class TestCTDCDatasetScraper:
    def test_init(self):
        scraper = CTDCDatasetScraper()
        assert scraper.name == "ctdc_dataset"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = CTDCDatasetScraper()
        record = {
            "source_name": "CTDC",
            "indicator": "trafficking",
            "report_title": "Global Synthetic Dataset",
            "country": "Pakistan",
            "gender": "Female",
            "age_group": "9-17",
            "exploitation_type": "Sexual Exploitation",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = CTDCDatasetScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_source(self):
        scraper = CTDCDatasetScraper()
        record = {"indicator": "trafficking", "country": "Pakistan"}
        assert scraper.validate(record) is False

    def test_validate_no_detail_fields(self):
        """Validate fails if no demographic/geographic fields are populated."""
        scraper = CTDCDatasetScraper()
        record = {
            "source_name": "CTDC",
            "indicator": "trafficking",
        }
        assert scraper.validate(record) is False

    def test_validate_with_country_only(self):
        scraper = CTDCDatasetScraper()
        record = {
            "source_name": "CTDC",
            "indicator": "trafficking",
            "country": "Pakistan",
        }
        assert scraper.validate(record) is True

    @pytest.mark.asyncio
    async def test_scrape(self, tmp_path, monkeypatch):
        """Test scrape with mocked downloader functions."""
        csv_path = tmp_path / "ctdc_raw.csv"
        filtered_path = tmp_path / "ctdc_pak.csv"
        csv_path.write_text("header\nrow1\n", encoding="utf-8")
        filtered_path.write_text("header\nrow1\n", encoding="utf-8")

        async def mock_download():
            return csv_path

        def mock_filter(path):
            return filtered_path

        def mock_parse(path):
            return [
                {
                    "trafficking_type": "forced_labor",
                    "year_of_registration": "2022",
                    "country_of_exploitation": "Pakistan",
                    "gender": "Female",
                    "age_group": "9-17",
                    "exploitation_type": "Domestic Servitude",
                    "means_of_control": "Debt Bondage",
                    "country_of_citizenship": "Pakistan",
                },
            ]

        monkeypatch.setattr(
            "data.scrapers.international.ctdc_dataset.download_ctdc_dataset",
            mock_download,
        )
        monkeypatch.setattr(
            "data.scrapers.international.ctdc_dataset.filter_pakistan_records",
            mock_filter,
        )
        monkeypatch.setattr(
            "data.scrapers.international.ctdc_dataset.parse_ctdc_records",
            mock_parse,
        )

        scraper = CTDCDatasetScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["source_name"] == "CTDC"
        assert results[0]["indicator"] == "forced_labor"
        assert results[0]["gender"] == "Female"
        await scraper.close()
