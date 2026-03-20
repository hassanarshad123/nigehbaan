"""Tests for HDX boundaries downloader."""

import json
from pathlib import Path

import pytest

from data.downloaders.hdx_boundaries import validate_geojson


class TestHDXBoundaries:
    def test_validate_geojson_valid(self, tmp_path, sample_geojson):
        file_path = tmp_path / "test.geojson"
        file_path.write_text(json.dumps(sample_geojson))
        assert validate_geojson(file_path) is True

    def test_validate_geojson_empty(self, tmp_path):
        file_path = tmp_path / "empty.geojson"
        file_path.write_text("{}")
        assert validate_geojson(file_path) is False

    def test_validate_geojson_no_features(self, tmp_path):
        file_path = tmp_path / "no_features.geojson"
        file_path.write_text(json.dumps({"type": "FeatureCollection", "features": []}))
        assert validate_geojson(file_path) is False

    def test_validate_geojson_nonexistent(self):
        assert validate_geojson(Path("nonexistent.geojson")) is False
