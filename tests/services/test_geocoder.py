"""Tests for the PakistanGeocoder service.

These tests exercise the pure-logic parts of the geocoder:
gazetteer loading, exact lookups, fuzzy matching, and match_district.
No database or network access is needed.
"""

import json
import pytest

from app.services.geocoder import PakistanGeocoder


# ---------- fixtures ----------


SAMPLE_GAZETTEER = {
    "lahore": {"lat": 31.5497, "lon": 74.3436, "pcode": "PK0403"},
    "karachi": {"lat": 24.8607, "lon": 67.0011, "pcode": "PK0202"},
    "peshawar": {"lat": 34.0151, "lon": 71.5249, "pcode": "PK0301"},
    "faisalabad": {"lat": 31.4504, "lon": 73.1350, "pcode": "PK0404"},
    "quetta": {"lat": 30.1798, "lon": 66.9750, "pcode": "PK0401"},
    "islamabad": {"lat": 33.6844, "lon": 73.0479, "pcode": "PK0101"},
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


# ---------- instantiation ----------


def test_instantiation_without_gazetteer():
    """Creating a geocoder without a gazetteer should produce an empty dict."""
    gc = PakistanGeocoder()
    assert gc.gazetteer == {}


def test_instantiation_with_gazetteer(geocoder):
    """Creating a geocoder with a gazetteer should load all entries."""
    assert len(geocoder.gazetteer) == len(SAMPLE_GAZETTEER)


def test_instantiation_with_invalid_path():
    """A non-existent gazetteer path should not raise; gazetteer stays empty."""
    gc = PakistanGeocoder(gazetteer_path="/nonexistent/path.json")
    assert gc.gazetteer == {}


# ---------- gazetteer lookup (exact match) ----------


@pytest.mark.asyncio
async def test_geocode_lahore(geocoder):
    """Exact lookup for 'lahore' should return correct coordinates."""
    result = await geocoder.geocode("lahore")
    assert result is not None
    lat, lon, confidence = result
    assert abs(lat - 31.5497) < 0.01
    assert abs(lon - 74.3436) < 0.01
    assert confidence == 1.0


@pytest.mark.asyncio
async def test_geocode_karachi(geocoder):
    """Exact lookup for 'karachi' should return correct coordinates."""
    result = await geocoder.geocode("karachi")
    assert result is not None
    lat, lon, confidence = result
    assert abs(lat - 24.8607) < 0.01
    assert abs(lon - 67.0011) < 0.01
    assert confidence == 1.0


@pytest.mark.asyncio
async def test_geocode_peshawar(geocoder):
    """Exact lookup for 'peshawar' should return correct coordinates."""
    result = await geocoder.geocode("peshawar")
    assert result is not None
    lat, lon, confidence = result
    assert abs(lat - 34.0151) < 0.01
    assert abs(lon - 71.5249) < 0.01
    assert confidence == 1.0


@pytest.mark.asyncio
async def test_geocode_case_insensitive(geocoder):
    """Gazetteer lookup should be case-insensitive."""
    result = await geocoder.geocode("LAHORE")
    assert result is not None
    assert result[2] == 1.0


@pytest.mark.asyncio
async def test_geocode_whitespace_tolerance(geocoder):
    """Leading and trailing whitespace should be stripped."""
    result = await geocoder.geocode("  karachi  ")
    assert result is not None
    assert result[2] == 1.0


# ---------- match_district ----------


def test_match_district_exact(geocoder):
    """Exact district name match should return the pcode."""
    pcode = geocoder.match_district("lahore")
    assert pcode == "PK0403"


def test_match_district_case_insensitive(geocoder):
    """match_district should be case-insensitive."""
    pcode = geocoder.match_district("KARACHI")
    assert pcode == "PK0202"


def test_match_district_peshawar(geocoder):
    """match_district for Peshawar should return correct pcode."""
    pcode = geocoder.match_district("peshawar")
    assert pcode == "PK0301"


# ---------- fuzzy / partial matching ----------


def test_match_district_partial_name(geocoder):
    """Partial name (substring) match should still find the district."""
    # "faisal" is a substring of "faisalabad"
    pcode = geocoder.match_district("faisal")
    assert pcode is not None
    assert pcode == "PK0404"


def test_match_district_containing_name(geocoder):
    """If the input contains a gazetteer name, match should succeed."""
    # "lahore district" contains "lahore"
    pcode = geocoder.match_district("lahore district")
    assert pcode is not None
    assert pcode == "PK0403"


# ---------- unknown location ----------


def test_match_district_unknown_returns_none(geocoder):
    """An unrecognised location name should return None."""
    pcode = geocoder.match_district("atlantis")
    assert pcode is None


@pytest.mark.asyncio
async def test_geocode_unknown_without_network(geocoder):
    """Unknown location with no Nominatim mock should return None.

    We don't mock Nominatim here, so the HTTP call will fail and
    the geocoder should fall back to returning None.
    """
    # Use respx to block all external requests
    import respx

    with respx.mock(assert_all_called=False) as router:
        router.route().respond(status_code=500)
        result = await geocoder.geocode("unknown_place_xyz")
        assert result is None
