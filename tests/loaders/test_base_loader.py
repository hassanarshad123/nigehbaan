"""Tests for the base loader."""

import json
from pathlib import Path

import pytest

from data.loaders.base_loader import BaseLoader


class TestLoader(BaseLoader):
    name = "test_loader"
    source_dir = "test_source"
    table_name = "test_table"

    def transform(self, raw_record):
        if not raw_record.get("valid"):
            return None
        return {"id": raw_record["id"], "value": raw_record["value"]}

    def validate(self, record):
        return bool(record.get("id"))


class TestBaseLoader:
    def test_init(self, tmp_path):
        loader = TestLoader(raw_base_dir=tmp_path)
        assert loader.loaded_count == 0
        assert loader.skipped_count == 0

    def test_discover_files(self, tmp_path):
        source_dir = tmp_path / "test_source"
        source_dir.mkdir()
        (source_dir / "file1.json").write_text("[]")
        (source_dir / "file2.json").write_text("[]")
        (source_dir / "file3.csv").write_text("")

        loader = TestLoader(raw_base_dir=tmp_path)
        files = loader.discover_files("json")
        assert len(files) == 2

    def test_read_json(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}]
        file_path.write_text(json.dumps(data))

        loader = TestLoader(raw_base_dir=tmp_path)
        records = loader.read_json(file_path)
        assert len(records) == 2

    def test_transform_filters_invalid(self):
        loader = TestLoader()
        assert loader.transform({"id": 1, "value": "a", "valid": True}) is not None
        assert loader.transform({"id": 1, "value": "a"}) is None

    @pytest.mark.asyncio
    async def test_run_pipeline(self, tmp_path):
        source_dir = tmp_path / "test_source"
        source_dir.mkdir()

        data = [
            {"id": 1, "value": "a", "valid": True},
            {"id": 2, "value": "b", "valid": True},
            {"id": 3, "value": "c", "valid": False},
        ]
        (source_dir / "data.json").write_text(json.dumps(data))

        loader = TestLoader(raw_base_dir=tmp_path)
        result = await loader.run()
        assert result["loaded"] == 2
        assert result["skipped"] == 1


class TestSpecificLoaders:
    def test_news_loader_transform(self):
        from data.loaders.news_loader import NewsLoader
        loader = NewsLoader()
        result = loader.transform({
            "url": "http://example.com/article",
            "title": "Test Article",
            "source": "dawn",
        })
        assert result is not None
        assert result["url"] == "http://example.com/article"
        assert result["source_name"] == "dawn"

    def test_news_loader_validate(self):
        from data.loaders.news_loader import NewsLoader
        loader = NewsLoader()
        assert loader.validate({"url": "http://x.com", "title": "Test"})
        assert not loader.validate({"url": "http://x.com"})

    def test_vulnerability_loader_transform(self):
        from data.loaders.vulnerability_loader import VulnerabilityLoader
        loader = VulnerabilityLoader()
        result = loader.transform({
            "indicator_code": "NY.GDP.PCAP.CD",
            "indicator_name": "GDP per capita",
            "year": 2023,
            "value": 1505.0,
        })
        assert result is not None
        assert result["indicator_code"] == "NY.GDP.PCAP.CD"

    def test_kilns_loader_validate(self):
        from data.loaders.kilns_loader import KilnsLoader
        loader = KilnsLoader()
        assert loader.validate({"latitude": 31.5, "longitude": 74.3})
        assert not loader.validate({"latitude": 0.0, "longitude": 0.0})  # Outside Pakistan
        assert not loader.validate({"latitude": None, "longitude": None})

    def test_tip_loader_transform(self):
        from data.loaders.tip_loader import TIPLoader
        loader = TIPLoader()
        result = loader.transform({
            "year": 2024,
            "tier_ranking": "Tier 2 Watch List",
            "investigations": 35,
        })
        assert result is not None
        assert result["year"] == 2024
        assert result["tier_ranking"] == "Tier 2 Watch List"
