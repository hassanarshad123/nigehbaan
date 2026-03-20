"""Tests for BaseAPIScraper."""

from pathlib import Path

import pytest

from data.scrapers.base_api_scraper import BaseAPIScraper


class MockAPIScraper(BaseAPIScraper):
    """Concrete implementation for testing."""

    name = "mock_api"
    source_url = "https://api.example.com/data"
    schedule = "0 0 1 */3 *"
    priority = "P1"

    async def scrape(self):
        data = await self.fetch_json(self.source_url)
        return [{"source_name": self.name, "indicator": "test", "value": len(data)}]

    def validate(self, record):
        return bool(record.get("source_name") and record.get("indicator"))


class TestBaseAPIScraper:
    @pytest.mark.asyncio
    async def test_fetch_json(self, mock_http):
        mock_http.get("https://api.example.com/data").respond(
            200, json={"results": [1, 2, 3]}
        )
        scraper = MockAPIScraper()
        scraper.rate_limit_delay = 0
        result = await scraper.fetch_json("https://api.example.com/data")
        assert result == {"results": [1, 2, 3]}
        await scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_paginated_single_page(self, mock_http):
        mock_http.get("https://api.example.com/data").respond(
            200, json={"results": [{"id": 1}, {"id": 2}], "total": 2, "per_page": 50}
        )
        scraper = MockAPIScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.fetch_paginated(
            "https://api.example.com/data",
            results_key="results",
        )
        assert len(results) == 2
        await scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_csv_download(self, mock_http, raw_data_dir, monkeypatch):
        monkeypatch.setattr("data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir)
        csv_content = "name,value\nalpha,1\nbeta,2\n"
        mock_http.get("https://api.example.com/data.csv").respond(200, text=csv_content)

        scraper = MockAPIScraper()
        scraper.rate_limit_delay = 0
        path = await scraper.fetch_csv_download("https://api.example.com/data.csv")
        assert path.exists()
        assert "alpha" in path.read_text()
        await scraper.close()

    def test_parse_csv(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("name,value\nalpha,1\nbeta,2\n", encoding="utf-8")

        scraper = MockAPIScraper()
        records = scraper.parse_csv(csv_path)
        assert len(records) == 2
        assert records[0]["name"] == "alpha"
        assert records[1]["value"] == "2"

    def test_parse_csv_custom_delimiter(self, tmp_path):
        csv_path = tmp_path / "test.tsv"
        csv_path.write_text("name\tvalue\nalpha\t1\n", encoding="utf-8")

        scraper = MockAPIScraper()
        records = scraper.parse_csv(csv_path, delimiter="\t")
        assert len(records) == 1
        assert records[0]["name"] == "alpha"

    def test_validate(self):
        scraper = MockAPIScraper()
        assert scraper.validate({"source_name": "test", "indicator": "x"}) is True
        assert scraper.validate({}) is False
