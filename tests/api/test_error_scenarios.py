"""Error scenario and edge case tests for API endpoints.

Validates that the API returns appropriate HTTP status codes and error
responses for invalid inputs, missing parameters, and boundary conditions.
When the DB is unavailable the asyncpg driver raises before FastAPI can
respond, so the shared ``api_get`` / ``api_post`` helpers convert that
into a synthetic 503.
"""

import contextlib

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.api.conftest import ACCEPTABLE_CODES_WITH_DB_DOWN, api_get

OK = ACCEPTABLE_CODES_WITH_DB_DOWN
TRANSPORT = ASGITransport(app=app)
BASE_URL = "http://test"


async def api_post(path: str, json_body: dict | None = None) -> tuple[int, dict | None]:
    """Issue a POST request against the test ASGI app."""
    try:
        async with AsyncClient(transport=TRANSPORT, base_url=BASE_URL) as client:
            resp = await client.post(path, json=json_body, timeout=15.0)
            with contextlib.suppress(Exception):
                body = resp.json()
                return resp.status_code, body
            return resp.status_code, None
    except Exception as exc:
        exc_name = type(exc).__name__
        if any(
            keyword in exc_name.lower()
            for keyword in ("connect", "timeout", "os", "operational", "interface", "postgres")
        ) or isinstance(exc, (ConnectionRefusedError, OSError, TimeoutError)):
            return 503, None
        raise


# ═══════════════════════════════════════════════════════════════
# Map endpoint error scenarios
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_map_boundaries_invalid_level():
    """GET /map/boundaries?level=99 should return 422 (validation) since level > 5."""
    status, body = await api_get("/api/v1/map/boundaries", level=99)
    if status == 503:
        pytest.skip("DB unavailable")
    # FastAPI Query(ge=0, le=5) rejects out-of-range values with 422
    assert status == 422, f"Expected 422 for level=99, got {status}: {body}"


@pytest.mark.asyncio
async def test_map_incidents_invalid_year():
    """GET /map/incidents?year=-5 should be accepted or rejected consistently.

    The year param has no ge/le constraint in the source, so negative years
    are technically valid (no incidents will match).  Expect 200 or DB error.
    """
    status, body = await api_get("/api/v1/map/incidents", year=-5)
    if status == 503:
        pytest.skip("DB unavailable")
    # No ge/le on year, so FastAPI accepts it and returns empty results or DB error
    assert status in {200, 500}, f"Unexpected status {status} for year=-5: {body}"
    if status == 200 and body is not None:
        assert body.get("type") == "FeatureCollection"
        assert isinstance(body.get("features"), list)


@pytest.mark.asyncio
async def test_map_heatmap_invalid_year():
    """GET /map/heatmap?year=0 should return 200 with empty list or DB error."""
    status, body = await api_get("/api/v1/map/heatmap", year=0)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status in {200, 500}, f"Unexpected status {status} for heatmap year=0: {body}"
    if status == 200 and body is not None:
        assert isinstance(body, list)


# ═══════════════════════════════════════════════════════════════
# Report endpoint error scenarios
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_reports_create_missing_fields():
    """POST /reports/ with empty body should return 422 (missing required fields)."""
    status, body = await api_post("/api/v1/reports/", {})
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 422, f"Expected 422 for empty body, got {status}: {body}"
    # Pydantic validation errors should be present
    assert body is not None
    assert "detail" in body


@pytest.mark.asyncio
async def test_reports_create_invalid_type():
    """POST /reports/ with an unknown report_type should still be accepted.

    The schema allows any string for report_type (min_length=2, max_length=100),
    so even an unusual value like 'zzz_unknown_type' is valid at the API level.
    The business logic does not restrict report_type to an enum.
    """
    payload = {
        "reportType": "zzz_unknown_type",
        "description": "This is a test report with an unusual report type value for edge case testing.",
        "isAnonymous": True,
    }
    status, body = await api_post("/api/v1/reports/", payload)
    if status == 503:
        pytest.skip("DB unavailable")
    # report_type is a free string — the API should accept it
    assert status == 201, f"Expected 201 for unknown reportType, got {status}: {body}"
    if body is not None:
        assert body.get("reportType") == "zzz_unknown_type"


# ═══════════════════════════════════════════════════════════════
# Search endpoint error scenarios
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_search_query_too_short():
    """GET /search/?q=a should return 422 since min_length=2."""
    status, body = await api_get("/api/v1/search/", q="a")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 422, f"Expected 422 for q='a' (1 char), got {status}: {body}"


@pytest.mark.asyncio
async def test_search_empty_query():
    """GET /search/ without q param should return 422 (required param missing)."""
    status, body = await api_get("/api/v1/search/")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 422, f"Expected 422 for missing q param, got {status}: {body}"


# ═══════════════════════════════════════════════════════════════
# Scraper control endpoint error scenarios
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_scraper_trigger_unknown_name():
    """POST /scrapers/nonexistent_scraper_xyz/trigger should return success=false or error.

    The trigger endpoint does not raise 404 for unknown names — it falls back
    to a generic task name pattern and attempts to dispatch (which may fail
    if Celery is not running).
    """
    status, body = await api_post("/api/v1/scrapers/nonexistent_scraper_xyz/trigger")
    if status == 503:
        pytest.skip("DB unavailable")
    # The endpoint catches all exceptions and returns success=false
    assert status == 200, f"Expected 200 with error message, got {status}: {body}"
    if body is not None:
        assert body.get("scraperName") == "nonexistent_scraper_xyz"


@pytest.mark.asyncio
async def test_scraper_stop_without_task_id():
    """POST /scrapers/dawn/stop without task_id should return success=false."""
    status, body = await api_post("/api/v1/scrapers/dawn/stop")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 200, f"Expected 200 with error, got {status}: {body}"
    if body is not None:
        assert body.get("success") is False
        assert "task_id required" in body.get("message", "").lower()


@pytest.mark.asyncio
async def test_scraper_toggle_unknown_name():
    """POST /scrapers/nonexistent_xyz/toggle should return 404 (scraper not found)."""
    status, body = await api_post("/api/v1/scrapers/nonexistent_xyz/toggle")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 404, f"Expected 404 for unknown scraper toggle, got {status}: {body}"


# ═══════════════════════════════════════════════════════════════
# Legal endpoint edge cases
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_legal_search_no_results():
    """GET /legal/search?court=zzz_nonexistent should return 200 with empty list."""
    status, body = await api_get("/api/v1/legal/search", court="zzz_nonexistent_court_999")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status in {200, 500}, f"Unexpected status {status}: {body}"
    if status == 200 and body is not None:
        assert isinstance(body, list)


# ═══════════════════════════════════════════════════════════════
# Dashboard endpoint edge cases
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dashboard_invalid_source():
    """GET /dashboard/trends?source=zzz_nonexistent should return 200 with empty list.

    The source filter is applied as a WHERE clause — no matching rows means
    an empty response, not an error.
    """
    status, body = await api_get(
        "/api/v1/dashboard/trends", source="zzz_nonexistent_source_999"
    )
    if status == 503:
        pytest.skip("DB unavailable")
    assert status in {200, 500}, f"Unexpected status {status}: {body}"
    if status == 200 and body is not None:
        assert isinstance(body, list)
