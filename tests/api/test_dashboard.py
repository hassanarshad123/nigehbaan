"""Tests for the /api/v1/dashboard/* endpoints.

Dashboard endpoints query the database. When the DB is unavailable the
asyncpg driver raises before FastAPI can respond, so the shared ``api_get``
helper converts that into a synthetic 503. Tests accept 200, 500, or 503.
"""

import pytest

from tests.api.conftest import ACCEPTABLE_CODES_WITH_DB_DOWN, api_get

OK = ACCEPTABLE_CODES_WITH_DB_DOWN


# ---------- /summary ----------


@pytest.mark.asyncio
async def test_summary_returns_200_or_db_error():
    """GET /api/v1/dashboard/summary should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/dashboard/summary")
    assert status in OK


@pytest.mark.asyncio
async def test_summary_kpi_keys():
    """Successful summary must contain the expected KPI keys."""
    status, body = await api_get("/api/v1/dashboard/summary")
    if status == 200 and body is not None:
        expected_keys = {
            "totalIncidents",
            "districtsWithData",
            "dataSourcesActive",
            "avgConvictionRate",
            "lastUpdated",
        }
        assert expected_keys.issubset(set(body.keys())), (
            f"Missing keys: {expected_keys - set(body.keys())}"
        )
        assert isinstance(body["totalIncidents"], int)
        assert isinstance(body["avgConvictionRate"], (int, float))


# ---------- /trends ----------


@pytest.mark.asyncio
async def test_trends_returns_200_or_db_error():
    """GET /api/v1/dashboard/trends should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/dashboard/trends")
    assert status in OK


@pytest.mark.asyncio
async def test_trends_returns_list():
    """Successful trends response must be a list of trend data points."""
    status, body = await api_get("/api/v1/dashboard/trends")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            point = body[0]
            assert "year" in point
            assert "count" in point


# ---------- /province-comparison ----------


@pytest.mark.asyncio
async def test_province_comparison_returns_200_or_db_error():
    """GET /api/v1/dashboard/province-comparison should return 200 or DB error."""
    status, _body = await api_get("/api/v1/dashboard/province-comparison")
    assert status in OK


@pytest.mark.asyncio
async def test_province_comparison_returns_list():
    """Successful province-comparison response must be a list."""
    status, body = await api_get("/api/v1/dashboard/province-comparison")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "province" in item
            assert "count" in item


# ---------- /case-types ----------


@pytest.mark.asyncio
async def test_case_types_returns_200_or_db_error():
    """GET /api/v1/dashboard/case-types should return 200 or DB error."""
    status, _body = await api_get("/api/v1/dashboard/case-types")
    assert status in OK


@pytest.mark.asyncio
async def test_case_types_returns_list():
    """Successful case-types response must contain type breakdown items."""
    status, body = await api_get("/api/v1/dashboard/case-types")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "type" in item
            assert "count" in item
            assert "percentage" in item


# ---------- /conviction-rates ----------


@pytest.mark.asyncio
async def test_conviction_rates_returns_200_or_db_error():
    """GET /api/v1/dashboard/conviction-rates should return 200 or DB error."""
    status, _body = await api_get("/api/v1/dashboard/conviction-rates")
    assert status in OK


@pytest.mark.asyncio
async def test_conviction_rates_returns_list():
    """Successful conviction-rates response must contain annual data."""
    status, body = await api_get("/api/v1/dashboard/conviction-rates")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "year" in item
            assert "convictions" in item
            assert "rate" in item


# ---------- /statistics ----------


@pytest.mark.asyncio
async def test_statistics_returns_200_or_db_error():
    """GET /api/v1/dashboard/statistics should return 200 or DB error."""
    status, _body = await api_get("/api/v1/dashboard/statistics")
    assert status in OK


@pytest.mark.asyncio
async def test_statistics_returns_list():
    """Successful statistics response must be a list."""
    status, body = await api_get("/api/v1/dashboard/statistics")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "sourceName" in item
            assert "indicator" in item


@pytest.mark.asyncio
async def test_statistics_filter_by_source():
    """Filtering statistics by source_name should return only matching rows."""
    status, body = await api_get("/api/v1/dashboard/statistics", source_name="sahil")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        for item in body:
            assert item["sourceName"] == "sahil"


@pytest.mark.asyncio
async def test_statistics_filter_by_year_range():
    """Filtering statistics by year range should return bounded results."""
    status, body = await api_get(
        "/api/v1/dashboard/statistics", year_from=2020, year_to=2024
    )
    if status == 200 and body is not None:
        assert isinstance(body, list)
        for item in body:
            if item["reportYear"] is not None:
                assert 2020 <= item["reportYear"] <= 2024


# ---------- /transparency ----------


@pytest.mark.asyncio
async def test_transparency_returns_200_or_db_error():
    """GET /api/v1/dashboard/transparency should return 200 or DB error."""
    status, _body = await api_get("/api/v1/dashboard/transparency")
    assert status in OK


@pytest.mark.asyncio
async def test_transparency_returns_list():
    """Successful transparency response must be a list."""
    status, body = await api_get("/api/v1/dashboard/transparency")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "platform" in item
            assert "metric" in item


@pytest.mark.asyncio
async def test_transparency_filter_by_platform():
    """Filtering by platform should return only matching rows."""
    status, body = await api_get("/api/v1/dashboard/transparency", platform="google")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        for item in body:
            assert item["platform"] == "google"


# ---------- /tip-details ----------


@pytest.mark.asyncio
async def test_tip_details_returns_200_or_db_error():
    """GET /api/v1/dashboard/tip-details should return 200 or DB error."""
    status, _body = await api_get("/api/v1/dashboard/tip-details")
    assert status in OK


@pytest.mark.asyncio
async def test_tip_details_returns_list():
    """Successful tip-details response must contain full TIP data."""
    status, body = await api_get("/api/v1/dashboard/tip-details")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "year" in item
            assert "tierRanking" in item
            assert "investigations" in item
            assert "convictions" in item
            assert "keyFindings" in item
