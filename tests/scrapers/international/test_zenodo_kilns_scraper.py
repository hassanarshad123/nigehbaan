"""Tests for the Zenodo brick kiln dataset scraper."""

import json

import pytest

from data.scrapers.international.zenodo_kilns_scraper import ZenodoKilnsScraper


class TestZenodoKilnsScraper:
    def test_init(self):
        scraper = ZenodoKilnsScraper()
        assert scraper.name == "zenodo_kilns_scraper"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = ZenodoKilnsScraper()
        record = {
            "source_name": "zenodo_kilns_scraper",
            "indicator": "total_kilns",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = ZenodoKilnsScraper()
        assert scraper.validate({}) is False

    def test_validate_negative_value(self):
        scraper = ZenodoKilnsScraper()
        record = {
            "source_name": "zenodo_kilns_scraper",
            "indicator": "total_kilns",
            "value": -1,
        }
        assert scraper.validate(record) is False

    def test_validate_missing_indicator(self):
        scraper = ZenodoKilnsScraper()
        record = {"source_name": "zenodo_kilns_scraper", "value": 100}
        assert scraper.validate(record) is False

    def test_load_features(self, tmp_path):
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [72.5, 31.5]},
                    "properties": {"id": 1},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [73.0, 31.0]},
                    "properties": {"id": 2},
                },
            ],
        }
        path = tmp_path / "kilns.geojson"
        path.write_text(json.dumps(geojson), encoding="utf-8")

        features = ZenodoKilnsScraper._load_features(path)
        assert len(features) == 2

    def test_load_features_invalid_file(self, tmp_path):
        path = tmp_path / "bad.geojson"
        path.write_text("not json", encoding="utf-8")

        features = ZenodoKilnsScraper._load_features(path)
        assert features == []

    def test_count_by_province(self):
        features = [
            # Punjab point
            {
                "geometry": {"type": "Point", "coordinates": [72.5, 31.5]},
                "properties": {},
            },
            # Sindh point
            {
                "geometry": {"type": "Point", "coordinates": [68.0, 26.0]},
                "properties": {},
            },
            # Another Punjab point
            {
                "geometry": {"type": "Point", "coordinates": [73.0, 30.0]},
                "properties": {},
            },
        ]
        counts = ZenodoKilnsScraper._count_by_province(features)
        assert counts.get("Punjab", 0) == 2
        assert counts.get("Sindh", 0) == 1

    @pytest.mark.asyncio
    async def test_scrape(self, tmp_path, monkeypatch):
        """Test scrape with mocked downloader functions."""
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [72.5, 31.5]},
                    "properties": {"id": 1},
                },
            ],
        }
        geojson_path = tmp_path / "kilns.geojson"
        geojson_path.write_text(json.dumps(geojson), encoding="utf-8")

        async def mock_download(**kwargs):
            return geojson_path

        def mock_validate(path):
            return True

        monkeypatch.setattr(
            "data.scrapers.international.zenodo_kilns_scraper.RAW_KILNS_DIR",
            tmp_path,
        )
        monkeypatch.setattr(
            "data.downloaders.zenodo_kilns.download_kiln_dataset",
            mock_download,
        )
        monkeypatch.setattr(
            "data.downloaders.zenodo_kilns.validate_kiln_geojson",
            mock_validate,
        )

        scraper = ZenodoKilnsScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]["indicator"] == "total_kilns"
        assert results[0]["value"] == 1
        await scraper.close()
