"""Tests for the SpatialAnalyzer service.

These tests exercise initialization and query methods by mocking
the async database session.  No real database or PostGIS is required.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.spatial_analysis import SpatialAnalyzer


# ---------- helpers ----------


def _make_mock_row(mapping: dict) -> MagicMock:
    """Create a mock SQLAlchemy row with a _mapping attribute."""
    row = MagicMock()
    row._mapping = mapping
    return row


def _make_mock_session(rows: list[dict] | None = None) -> AsyncMock:
    """Create a mock AsyncSession that returns the given rows on execute."""
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [_make_mock_row(r) for r in (rows or [])]
    session.execute = AsyncMock(return_value=mock_result)
    return session


# ---------- fixtures ----------


@pytest.fixture
def mock_session():
    """Return a mock AsyncSession with no rows."""
    return _make_mock_session([])


@pytest.fixture
def analyzer(mock_session):
    """Return a SpatialAnalyzer with a mocked session."""
    return SpatialAnalyzer(session=mock_session)


# ---------- init ----------


def test_analyzer_init():
    """SpatialAnalyzer should store the session."""
    session = AsyncMock()
    sa = SpatialAnalyzer(session=session)
    assert sa.session is session


# ---------- find_incidents_near_kilns ----------


@pytest.mark.asyncio
async def test_find_incidents_near_kilns_empty():
    """Empty result set should return an empty list."""
    session = _make_mock_session([])
    sa = SpatialAnalyzer(session=session)
    results = await sa.find_incidents_near_kilns()
    assert results == []
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_incidents_near_kilns_with_data():
    """Should return dicts with incident_id, kiln_id, and distance_m."""
    rows = [
        {"incident_id": 1, "kiln_id": 10, "distance_m": 500.0},
        {"incident_id": 2, "kiln_id": 10, "distance_m": 1200.5},
    ]
    session = _make_mock_session(rows)
    sa = SpatialAnalyzer(session=session)
    results = await sa.find_incidents_near_kilns(radius_m=5000)
    assert len(results) == 2
    assert results[0]["incident_id"] == 1
    assert results[1]["distance_m"] == 1200.5


@pytest.mark.asyncio
async def test_find_incidents_near_kilns_passes_radius():
    """The radius parameter should be forwarded to the query."""
    session = _make_mock_session([])
    sa = SpatialAnalyzer(session=session)
    await sa.find_incidents_near_kilns(radius_m=25_000)
    # Verify the execute was called with the radius parameter
    call_args = session.execute.call_args
    assert call_args[0][1]["radius"] == 25_000


@pytest.mark.asyncio
async def test_find_incidents_near_kilns_default_radius():
    """Default radius should be 10,000 metres."""
    session = _make_mock_session([])
    sa = SpatialAnalyzer(session=session)
    await sa.find_incidents_near_kilns()
    call_args = session.execute.call_args
    assert call_args[0][1]["radius"] == 10_000


# ---------- calculate_district_density ----------


@pytest.mark.asyncio
async def test_calculate_district_density_empty():
    """Empty result set should return an empty list."""
    session = _make_mock_session([])
    sa = SpatialAnalyzer(session=session)
    results = await sa.calculate_district_density()
    assert results == []


@pytest.mark.asyncio
async def test_calculate_district_density_with_data():
    """Should return dicts with district_pcode, incident_count, population, per_100k."""
    rows = [
        {
            "district_pcode": "PK0403",
            "name_en": "Lahore",
            "incident_count": 50,
            "population": 11_000_000,
            "per_100k": 0.45,
        },
        {
            "district_pcode": "PK0202",
            "name_en": "Karachi South",
            "incident_count": 30,
            "population": 5_000_000,
            "per_100k": 0.60,
        },
    ]
    session = _make_mock_session(rows)
    sa = SpatialAnalyzer(session=session)
    results = await sa.calculate_district_density()
    assert len(results) == 2
    assert results[0]["district_pcode"] == "PK0403"
    assert results[1]["per_100k"] == 0.60


@pytest.mark.asyncio
async def test_calculate_district_density_no_params():
    """calculate_district_density takes no parameters (query is static)."""
    session = _make_mock_session([])
    sa = SpatialAnalyzer(session=session)
    await sa.calculate_district_density()
    # Should be called with just the query text, no params dict
    call_args = session.execute.call_args
    assert len(call_args[0]) == 1  # only the text() query, no params


# ---------- identify_hotspot_clusters ----------


@pytest.mark.asyncio
async def test_identify_hotspot_clusters_empty():
    """Empty result set should return an empty list."""
    session = _make_mock_session([])
    sa = SpatialAnalyzer(session=session)
    results = await sa.identify_hotspot_clusters()
    assert results == []
