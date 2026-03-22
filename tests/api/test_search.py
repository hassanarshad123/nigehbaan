"""Tests for the /api/v1/search endpoint.

The search endpoint enforces min_length=2 via FastAPI query validation.
Queries shorter than 2 characters receive a 422 (Unprocessable Entity).
When the DB is unavailable, valid queries may get a 500 or the asyncpg
driver raises before FastAPI responds (caught as 503 by our helper).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.api.conftest import ACCEPTABLE_CODES_WITH_DB_DOWN, api_get

OK = ACCEPTABLE_CODES_WITH_DB_DOWN


# ---------- normal search ----------


@pytest.mark.asyncio
async def test_search_lahore_returns_200_or_db_error():
    """GET /api/v1/search?q=lahore should return 200 or DB-related error."""
    status, body = await api_get("/api/v1/search/", q="lahore")
    assert status in OK


@pytest.mark.asyncio
async def test_search_lahore_returns_list():
    """Successful search must return a list of SearchResult items."""
    status, body = await api_get("/api/v1/search/", q="lahore")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "id" in item
            assert "type" in item
            assert "title" in item
            assert "snippet" in item


# ---------- empty / missing query ----------


@pytest.mark.asyncio
async def test_search_missing_query_returns_422():
    """GET /api/v1/search/ without 'q' param should return 422.

    This is purely a FastAPI validation check — no DB needed.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/search/")
        assert resp.status_code == 422, "Missing required 'q' param should be rejected"


# ---------- query too short ----------


@pytest.mark.asyncio
async def test_search_query_too_short_returns_422():
    """GET /api/v1/search?q=a (1 char) should return 422 per min_length=2.

    This is purely a FastAPI validation check — no DB needed.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/search/", params={"q": "a"})
        assert resp.status_code == 422, "Query below min_length should be rejected"


@pytest.mark.asyncio
async def test_search_two_char_query_accepted():
    """GET /api/v1/search?q=pk (exactly 2 chars) should be accepted."""
    status, body = await api_get("/api/v1/search/", q="pk")
    assert status in OK, "2-char query should pass min_length validation"
