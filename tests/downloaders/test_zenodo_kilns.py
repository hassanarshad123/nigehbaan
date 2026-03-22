"""Tests for the Zenodo brick kiln dataset downloader."""

import json
from pathlib import Path


from data.downloaders.zenodo_kilns import (
    validate_kiln_geojson,
    _PAK_LAT_MIN,
    _PAK_LAT_MAX,
    _PAK_LNG_MIN,
    _PAK_LNG_MAX,
)


def _make_kiln_geojson(num_features: int, in_pakistan: bool = True) -> dict:
    """Build a synthetic kiln GeoJSON with the given number of features."""
    features = []
    for i in range(num_features):
        if in_pakistan:
            lng = 71.0 + (i * 0.001)
            lat = 31.0 + (i * 0.001)
        else:
            lng = 10.0 + (i * 0.001)
            lat = 10.0 + (i * 0.001)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
            "properties": {"confidence": 0.95},
        })
    return {"type": "FeatureCollection", "features": features}


class TestValidateKilnGeojson:
    """Unit tests for validate_kiln_geojson."""

    def test_valid_large_dataset(self, tmp_path: Path):
        geojson = _make_kiln_geojson(10_500, in_pakistan=True)
        file_path = tmp_path / "kilns.geojson"
        file_path.write_text(json.dumps(geojson), encoding="utf-8")
        assert validate_kiln_geojson(file_path) is True

    def test_too_few_features_returns_false(self, tmp_path: Path):
        geojson = _make_kiln_geojson(100, in_pakistan=True)
        file_path = tmp_path / "small_kilns.geojson"
        file_path.write_text(json.dumps(geojson), encoding="utf-8")
        assert validate_kiln_geojson(file_path) is False

    def test_nonexistent_file_returns_false(self):
        assert validate_kiln_geojson(Path("/nonexistent/kilns.geojson")) is False

    def test_invalid_json_returns_false(self, tmp_path: Path):
        file_path = tmp_path / "bad.geojson"
        file_path.write_text("not valid json {{{", encoding="utf-8")
        assert validate_kiln_geojson(file_path) is False

    def test_wrong_type_returns_false(self, tmp_path: Path):
        file_path = tmp_path / "wrong_type.geojson"
        file_path.write_text(json.dumps({"type": "Feature"}), encoding="utf-8")
        assert validate_kiln_geojson(file_path) is False

    def test_points_outside_pakistan_fail_validation(self, tmp_path: Path):
        geojson = _make_kiln_geojson(10_500, in_pakistan=False)
        file_path = tmp_path / "outside.geojson"
        file_path.write_text(json.dumps(geojson), encoding="utf-8")
        assert validate_kiln_geojson(file_path) is False


class TestPakistanBounds:
    """Verify the Pakistan bounding box constants are reasonable."""

    def test_latitude_range(self):
        assert _PAK_LAT_MIN < _PAK_LAT_MAX
        assert 23.0 <= _PAK_LAT_MIN <= 24.5
        assert 36.5 <= _PAK_LAT_MAX <= 38.0

    def test_longitude_range(self):
        assert _PAK_LNG_MIN < _PAK_LNG_MAX
        assert 59.0 <= _PAK_LNG_MIN <= 61.0
        assert 76.5 <= _PAK_LNG_MAX <= 78.0
