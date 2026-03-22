"""Tests for the UNOSAT 2022 flood extent downloader utilities."""


from data.downloaders.flood_extent import (
    classify_flood_impact,
    calculate_district_flood_percentage,
)


class TestClassifyFloodImpact:
    """Unit tests for classify_flood_impact severity buckets."""

    def test_severe_above_50(self):
        result = classify_flood_impact({"PK0101": 75.0})
        assert result["PK0101"] == "severe"

    def test_high_between_25_and_50(self):
        result = classify_flood_impact({"PK0201": 35.0})
        assert result["PK0201"] == "high"

    def test_moderate_between_10_and_25(self):
        result = classify_flood_impact({"PK0301": 15.0})
        assert result["PK0301"] == "moderate"

    def test_low_between_1_and_10(self):
        result = classify_flood_impact({"PK0401": 5.0})
        assert result["PK0401"] == "low"

    def test_minimal_below_1(self):
        result = classify_flood_impact({"PK0501": 0.5})
        assert result["PK0501"] == "minimal"

    def test_zero_is_minimal(self):
        result = classify_flood_impact({"PK0601": 0.0})
        assert result["PK0601"] == "minimal"

    def test_boundary_at_50(self):
        # Exactly 50 is NOT > 50, so it should be "high"
        result = classify_flood_impact({"PK0701": 50.0})
        assert result["PK0701"] == "high"

    def test_boundary_at_25(self):
        # Exactly 25 is NOT > 25, so should be "moderate"
        result = classify_flood_impact({"PK0801": 25.0})
        assert result["PK0801"] == "moderate"

    def test_multiple_districts(self):
        data = {
            "PK0101": 80.0,
            "PK0201": 30.0,
            "PK0301": 12.0,
            "PK0401": 3.0,
            "PK0501": 0.1,
        }
        result = classify_flood_impact(data)
        assert result["PK0101"] == "severe"
        assert result["PK0201"] == "high"
        assert result["PK0301"] == "moderate"
        assert result["PK0401"] == "low"
        assert result["PK0501"] == "minimal"

    def test_empty_dict(self):
        result = classify_flood_impact({})
        assert result == {}


class TestCalculateDistrictFloodPercentage:
    """Tests for calculate_district_flood_percentage edge cases."""

    def test_returns_empty_when_no_shapefiles(self, tmp_path):
        """When no .shp files exist in flood_extent_path, return empty."""
        flood_dir = tmp_path / "flood"
        flood_dir.mkdir()
        boundaries = tmp_path / "boundaries.geojson"
        boundaries.write_text("{}", encoding="utf-8")

        result = calculate_district_flood_percentage(flood_dir, boundaries)
        assert result == {}

    def test_returns_empty_when_geopandas_missing(self, monkeypatch):
        """If geopandas is not available, function returns empty dict."""
        import builtins
        original_import = builtins.__import__

        def _mock_import(name, *args, **kwargs):
            if name == "geopandas":
                raise ImportError("mocked")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _mock_import)

        from pathlib import Path
        result = calculate_district_flood_percentage(
            Path("/nonexistent/flood"),
            Path("/nonexistent/boundaries"),
        )
        assert result == {}
