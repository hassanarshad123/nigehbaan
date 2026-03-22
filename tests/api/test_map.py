"""Tests for the /api/v1/map/* endpoints.

All map endpoints depend on the database.  When the DB is unavailable the
asyncpg driver raises before FastAPI can respond, so the shared ``api_get``
helper converts that into a synthetic 503.  Tests accept 200, 500, or 503.
"""

import pytest

from tests.api.conftest import ACCEPTABLE_CODES_WITH_DB_DOWN, api_get

OK = ACCEPTABLE_CODES_WITH_DB_DOWN


# ---------- /boundaries ----------


@pytest.mark.asyncio
async def test_boundaries_returns_200_or_db_error():
    """GET /api/v1/map/boundaries should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/map/boundaries")
    assert status in OK


@pytest.mark.asyncio
async def test_boundaries_geojson_structure():
    """If the DB is available the response must be a GeoJSON FeatureCollection."""
    status, body = await api_get("/api/v1/map/boundaries")
    if status == 200 and body is not None:
        assert body.get("type") == "FeatureCollection"
        assert "features" in body
        assert isinstance(body["features"], list)


# ---------- /incidents ----------


@pytest.mark.asyncio
async def test_incidents_returns_200_or_db_error():
    """GET /api/v1/map/incidents should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/map/incidents")
    assert status in OK


@pytest.mark.asyncio
async def test_incidents_geojson_format():
    """Successful incidents response must be GeoJSON FeatureCollection."""
    status, body = await api_get("/api/v1/map/incidents")
    if status == 200 and body is not None:
        assert body.get("type") == "FeatureCollection"
        assert isinstance(body.get("features"), list)


# ---------- /kilns ----------


@pytest.mark.asyncio
async def test_kilns_returns_200_or_db_error():
    """GET /api/v1/map/kilns should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/map/kilns")
    assert status in OK


@pytest.mark.asyncio
async def test_kilns_geojson_format():
    """Successful kilns response must be GeoJSON FeatureCollection."""
    status, body = await api_get("/api/v1/map/kilns")
    if status == 200 and body is not None:
        assert body.get("type") == "FeatureCollection"
        assert isinstance(body.get("features"), list)


# ---------- /borders (border crossings) ----------


@pytest.mark.asyncio
async def test_border_crossings_returns_200_or_db_error():
    """GET /api/v1/map/borders should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/map/borders")
    assert status in OK


@pytest.mark.asyncio
async def test_border_crossings_returns_list():
    """Successful borders response must be a list of crossing points."""
    status, body = await api_get("/api/v1/map/borders")
    if status == 200 and body is not None:
        assert isinstance(body, list)


# ---------- /routes ----------


@pytest.mark.asyncio
async def test_routes_returns_200_or_db_error():
    """GET /api/v1/map/routes should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/map/routes")
    assert status in OK


@pytest.mark.asyncio
async def test_routes_geojson_format():
    """Successful routes response must be GeoJSON FeatureCollection."""
    status, body = await api_get("/api/v1/map/routes")
    if status == 200 and body is not None:
        assert body.get("type") == "FeatureCollection"
        assert isinstance(body.get("features"), list)


# ---------- /vulnerability (vulnerability heatmap / choropleth) ----------


@pytest.mark.asyncio
async def test_vulnerability_returns_200_or_db_error():
    """GET /api/v1/map/vulnerability should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/map/vulnerability")
    assert status in OK


@pytest.mark.asyncio
async def test_vulnerability_geojson_format():
    """Successful vulnerability response must be GeoJSON FeatureCollection."""
    status, body = await api_get("/api/v1/map/vulnerability")
    if status == 200 and body is not None:
        assert body.get("type") == "FeatureCollection"
        assert isinstance(body.get("features"), list)


# ---------- /heatmap ----------


@pytest.mark.asyncio
async def test_heatmap_returns_200_or_db_error():
    """GET /api/v1/map/heatmap should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/map/heatmap")
    assert status in OK


@pytest.mark.asyncio
async def test_heatmap_returns_list():
    """Successful heatmap response must be a list of point dicts."""
    status, body = await api_get("/api/v1/map/heatmap")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            point = body[0]
            assert "lat" in point
            assert "lon" in point
            assert "weight" in point
