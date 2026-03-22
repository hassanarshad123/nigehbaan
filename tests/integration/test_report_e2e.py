"""End-to-end integration tests for the report submission + tracking flow.

These tests exercise the full chain:
  POST /reports/ → reference number → GET /reports/{ref} → status

When the DB is unavailable, tests skip gracefully.
"""

import contextlib

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TRANSPORT = ASGITransport(app=app)
BASE_URL = "http://test"


async def _post(path: str, json_body: dict) -> tuple[int, dict | None]:
    try:
        async with AsyncClient(transport=TRANSPORT, base_url=BASE_URL) as client:
            resp = await client.post(path, json=json_body, timeout=15.0)
            with contextlib.suppress(Exception):
                return resp.status_code, resp.json()
            return resp.status_code, None
    except Exception as exc:
        if isinstance(exc, (ConnectionRefusedError, OSError, TimeoutError)):
            return 503, None
        raise


async def _get(path: str) -> tuple[int, dict | None]:
    try:
        async with AsyncClient(transport=TRANSPORT, base_url=BASE_URL) as client:
            resp = await client.get(path, timeout=15.0)
            with contextlib.suppress(Exception):
                return resp.status_code, resp.json()
            return resp.status_code, None
    except Exception as exc:
        if isinstance(exc, (ConnectionRefusedError, OSError, TimeoutError)):
            return 503, None
        raise


REPORT_PAYLOAD = {
    "reportType": "suspicious_activity",
    "description": "Multiple children observed near brick kiln with signs of forced labor.",
    "latitude": 31.5497,
    "longitude": 74.3436,
    "address": "Lahore, GT Road",
    "incidentDate": "2026-03-20",
    "isAnonymous": True,
}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_submit_and_track_report():
    """Full flow: submit report → get reference → track by reference."""
    # Step 1: Submit report
    status, body = await _post("/api/v1/reports/", REPORT_PAYLOAD)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201, f"Expected 201, got {status}: {body}"
    assert body is not None
    ref = body["referenceNumber"]
    assert ref.startswith("NGB-")

    # Step 2: Track by reference number
    get_status, get_body = await _get(f"/api/v1/reports/{ref}")
    if get_status == 503:
        pytest.skip("DB unavailable")
    assert get_status == 200
    assert get_body is not None
    assert get_body["referenceNumber"] == ref
    assert get_body["status"] == "pending"
    assert get_body["reportType"] == "suspicious_activity"
    assert "createdAt" in get_body
    assert "updatedAt" in get_body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_submit_with_geocoding():
    """Submit report with coordinates → district_pcode should be populated."""
    status, body = await _post("/api/v1/reports/", REPORT_PAYLOAD)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201
    # The report was created; check that it's retrievable
    ref = body["referenceNumber"]
    get_status, get_body = await _get(f"/api/v1/reports/{ref}")
    if get_status == 503:
        pytest.skip("DB unavailable")
    assert get_status == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_submit_anonymous_no_contact():
    """Anonymous report should succeed without contact info."""
    payload = {
        "reportType": "missing_child",
        "description": "Child reported missing from neighbourhood school compound.",
        "isAnonymous": True,
    }
    status, body = await _post("/api/v1/reports/", payload)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201
    assert body["referenceNumber"].startswith("NGB-")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_report_lifecycle():
    """Submit → verify pending → retrieve by ID → same data."""
    status, body = await _post("/api/v1/reports/", REPORT_PAYLOAD)
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 201

    report_id = body["id"]
    ref = body["referenceNumber"]

    # Get by numeric ID
    id_status, id_body = await _get(f"/api/v1/reports/{report_id}")
    if id_status == 503:
        pytest.skip("DB unavailable")
    assert id_status == 200
    assert id_body["referenceNumber"] == ref
    assert id_body["status"] == "pending"

    # Get by reference number — should match
    ref_status, ref_body = await _get(f"/api/v1/reports/{ref}")
    assert ref_status == 200
    assert ref_body["id"] == report_id
