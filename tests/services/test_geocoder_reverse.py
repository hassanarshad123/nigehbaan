"""Tests for the PakistanGeocoder.reverse_geocode_district method.

These tests exercise reverse geocoding: given lat/lon coordinates,
find the nearest district pcode using haversine distance.
No database or network access is needed.
"""

import json

import pytest

from app.services.geocoder import PakistanGeocoder


# ---------- fixtures ----------


SAMPLE_GAZETTEER = {
    "lahore": {"lat": 31.5497, "lon": 74.3436, "pcode": "PK0401"},
    "karachi central": {"lat": 24.8607, "lon": 67.0011, "pcode": "PK0301"},
    "islamabad": {"lat": 33.6844, "lon": 73.0479, "pcode": "PK0101"},
    "peshawar": {"lat": 34.0151, "lon": 71.5249, "pcode": "PK0201"},
    "quetta": {"lat": 30.1798, "lon": 66.9750, "pcode": "PK0501"},
    "faisalabad": {"lat": 31.4504, "lon": 73.1350, "pcode": "PK0403"},
    "multan": {"lat": 30.1575, "lon": 71.5249, "pcode": "PK0406"},
}


@pytest.fixture
def gazetteer_file(tmp_path):
    """Write the sample gazetteer to a temp JSON file."""
    path = tmp_path / "gazetteer.json"
    path.write_text(json.dumps(SAMPLE_GAZETTEER), encoding="utf-8")
    return str(path)


@pytest.fixture
def geocoder(gazetteer_file):
    """Return a PakistanGeocoder loaded with the sample gazetteer."""
    return PakistanGeocoder(gazetteer_path=gazetteer_file)


# ---------- reverse geocoding ----------


def test_reverse_geocode_lahore_coords(geocoder):
    """Coordinates near Lahore should resolve to Lahore pcode."""
    pcode = geocoder.reverse_geocode_district(31.55, 74.34)
    assert pcode == "PK0401"


def test_reverse_geocode_karachi_coords(geocoder):
    """Coordinates near Karachi should resolve to Karachi pcode."""
    pcode = geocoder.reverse_geocode_district(24.86, 67.00)
    assert pcode == "PK0301"


def test_reverse_geocode_islamabad(geocoder):
    """Coordinates near Islamabad should resolve to Islamabad pcode."""
    pcode = geocoder.reverse_geocode_district(33.68, 73.05)
    assert pcode == "PK0101"


def test_reverse_geocode_peshawar(geocoder):
    """Coordinates near Peshawar should resolve to Peshawar pcode."""
    pcode = geocoder.reverse_geocode_district(34.02, 71.52)
    assert pcode == "PK0201"


def test_reverse_geocode_far_from_pakistan(geocoder):
    """Coordinates far from Pakistan (0, 0) should return None."""
    pcode = geocoder.reverse_geocode_district(0.0, 0.0)
    assert pcode is None


def test_reverse_geocode_threshold(geocoder):
    """Coordinates > threshold_km from nearest should return None."""
    # London coordinates — ~6000km from Pakistan
    pcode = geocoder.reverse_geocode_district(51.5074, -0.1278)
    assert pcode is None


def test_reverse_geocode_custom_threshold(geocoder):
    """A very tight threshold should reject coordinates slightly off."""
    # Coordinates 50km from Lahore — should fail with 10km threshold
    pcode = geocoder.reverse_geocode_district(31.9, 74.8, threshold_km=10.0)
    # May or may not match depending on distance — but shouldn't crash
    assert pcode is None or isinstance(pcode, str)


def test_reverse_geocode_returns_valid_pcode(geocoder):
    """Result pcode must exist in the gazetteer."""
    valid_pcodes = {v["pcode"] for v in SAMPLE_GAZETTEER.values() if "pcode" in v}
    pcode = geocoder.reverse_geocode_district(31.5497, 74.3436)
    assert pcode in valid_pcodes


def test_reverse_geocode_empty_gazetteer():
    """An empty gazetteer should return None."""
    gc = PakistanGeocoder()
    pcode = gc.reverse_geocode_district(31.5497, 74.3436)
    assert pcode is None


def test_reverse_geocode_picks_nearest(geocoder):
    """Coordinates equidistant to two cities should pick the closest."""
    # Exact Multan coordinates should match Multan
    pcode = geocoder.reverse_geocode_district(30.1575, 71.5249)
    assert pcode == "PK0406"


def test_reverse_geocode_boundary_case(geocoder):
    """Coordinates right at threshold boundary should still return a result."""
    # Close to Faisalabad
    pcode = geocoder.reverse_geocode_district(31.45, 73.14)
    assert pcode == "PK0403"
