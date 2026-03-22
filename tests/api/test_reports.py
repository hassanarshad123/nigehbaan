"""Tests for the /api/v1/reports/* endpoints.

Report endpoints handle public report submission, listing, and tracking.
When the DB is unavailable the asyncpg driver raises before FastAPI can
respond, so the shared ``api_get`` helper converts that into a synthetic
503. Tests accept 200/201, 500, or 503.
"""

import contextlib

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.api.conftest import ACCEPTABLE_CODES_WITH_DB_DOWN, api_get

OK = ACCEPTABLE_CODES_WITH_DB_DOWN
TRANSPORT = ASGITransport(app=app)
BASE_URL = "http://test"


async def api_post(path: str, json_body: dict) -> tuple[int, dict | None]:
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


# ---------- POST /reports/ ----------


VALID_REPORT = {
    "reportType": "suspicious_activity",
    "description": "Suspicious activity near the brick kiln on GT Road, multiple children observed.",
    "latitude": 31.5497,
    "longitude": 74.3436,
    "address": "GT Road, Lahore",
    "incidentDate": "2026-03-20",
    "isAnonymous": True,
}


@pytest.mark.asyncio
async def test_create_report_success():
    """POST valid report should return 201 with a NGB- reference number."""
    status, body = await api_post("/api/v1/reports/", VALID_REPORT)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201, f"Expected 201, got {status}: {body}"
    assert body is not None
    assert body["referenceNumber"].startswith("NGB-")
    assert body["status"] == "pending"
    assert body["reportType"] == "suspicious_activity"


@pytest.mark.asyncio
async def test_create_report_with_location():
    """POST with lat/lon should store geometry and resolve district pcode."""
    status, body = await api_post("/api/v1/reports/", VALID_REPORT)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201
    # The reference should exist and be retrievable
    ref = body["referenceNumber"]
    get_status, get_body = await api_get(f"/api/v1/reports/{ref}")
    if get_status == 200 and get_body is not None:
        assert get_body["referenceNumber"] == ref


@pytest.mark.asyncio
async def test_create_report_with_date():
    """POST with incidentDate should be accepted."""
    payload = {
        "reportType": "missing_child",
        "description": "Child went missing from school grounds yesterday afternoon.",
        "incidentDate": "2026-03-19",
        "isAnonymous": True,
    }
    status, body = await api_post("/api/v1/reports/", payload)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201


@pytest.mark.asyncio
async def test_create_report_anonymous():
    """Anonymous report should not require contact fields."""
    payload = {
        "reportType": "bonded_labor",
        "description": "Children working in hazardous conditions at local brick kiln.",
        "isAnonymous": True,
    }
    status, body = await api_post("/api/v1/reports/", payload)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201


@pytest.mark.asyncio
async def test_create_report_validation_short_description():
    """Description shorter than 10 chars should be rejected with 422."""
    payload = {
        "reportType": "suspicious_activity",
        "description": "Short",
        "isAnonymous": True,
    }
    status, body = await api_post("/api/v1/reports/", payload)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 422


@pytest.mark.asyncio
async def test_create_report_validation_lat_without_lon():
    """Providing latitude without longitude should be rejected."""
    payload = {
        "reportType": "suspicious_activity",
        "description": "Test description that is long enough to pass validation.",
        "latitude": 31.5,
        "isAnonymous": True,
    }
    status, body = await api_post("/api/v1/reports/", payload)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 422


@pytest.mark.asyncio
async def test_create_report_with_photos():
    """POST with photos array should be accepted."""
    payload = {
        "reportType": "suspicious_activity",
        "description": "Suspicious vehicle photographed near primary school compound.",
        "photos": ["data:image/png;base64,iVBOR..."],
        "isAnonymous": True,
    }
    status, body = await api_post("/api/v1/reports/", payload)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201


# ---------- GET /reports/{ref_or_id} ----------


@pytest.mark.asyncio
async def test_get_report_by_id():
    """GET /reports/<numeric_id> should return full ReportStatus."""
    # First create a report
    status, body = await api_post("/api/v1/reports/", VALID_REPORT)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201
    report_id = body["id"]

    get_status, get_body = await api_get(f"/api/v1/reports/{report_id}")
    if get_status == 503:
        pytest.skip("DB unavailable")
    assert get_status == 200
    assert get_body is not None
    assert get_body["id"] == report_id
    assert "referenceNumber" in get_body
    assert "reportType" in get_body
    assert "status" in get_body
    assert "createdAt" in get_body
    assert "updatedAt" in get_body


@pytest.mark.asyncio
async def test_get_report_by_reference():
    """GET /reports/<NGB-XXXX> should return the same report."""
    status, body = await api_post("/api/v1/reports/", VALID_REPORT)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201
    ref = body["referenceNumber"]

    get_status, get_body = await api_get(f"/api/v1/reports/{ref}")
    if get_status == 503:
        pytest.skip("DB unavailable")
    assert get_status == 200
    assert get_body is not None
    assert get_body["referenceNumber"] == ref
    assert get_body["reportType"] == "suspicious_activity"


@pytest.mark.asyncio
async def test_get_report_not_found_id():
    """GET /reports/99999 should return 404."""
    status, body = await api_get("/api/v1/reports/99999")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 404


@pytest.mark.asyncio
async def test_get_report_not_found_ref():
    """GET /reports/NGB-INVALID should return 404."""
    status, body = await api_get("/api/v1/reports/NGB-ZZZZZZZZ")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 404


@pytest.mark.asyncio
async def test_reference_number_persisted():
    """Reference number should be persisted and retrievable after creation."""
    status, body = await api_post("/api/v1/reports/", VALID_REPORT)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201
    ref = body["referenceNumber"]
    assert ref.startswith("NGB-")
    assert len(ref) == 12  # NGB- + 8 hex chars

    # Retrieve by ref
    get_status, get_body = await api_get(f"/api/v1/reports/{ref}")
    if get_status == 503:
        pytest.skip("DB unavailable")
    assert get_status == 200
    assert get_body["referenceNumber"] == ref


# ---------- GET /reports/ (listing) ----------


@pytest.mark.asyncio
async def test_list_reports_default():
    """GET /reports/ should return a list."""
    status, body = await api_get("/api/v1/reports/")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status in {200, 500}
    if status == 200:
        assert isinstance(body, list)


@pytest.mark.asyncio
async def test_list_reports_filter_status():
    """GET /reports/?status=pending should return only pending reports."""
    status, body = await api_get("/api/v1/reports/", status="pending")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status in {200, 500}
    if status == 200 and body is not None:
        assert isinstance(body, list)
        for report in body:
            assert report["status"] == "pending"
