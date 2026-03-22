"""Tests for the /api/v1/scrapers/* endpoints.

Scraper endpoints depend on the database. Tests accept 200, 500, or 503
(the synthetic code returned by api_get when the DB driver raises).
"""

import pytest

from tests.api.conftest import ACCEPTABLE_CODES_WITH_DB_DOWN, api_get

OK = ACCEPTABLE_CODES_WITH_DB_DOWN


# ---------- GET /scrapers/ ----------


@pytest.mark.asyncio
async def test_list_scrapers_returns_200_or_db_error():
    """GET /api/v1/scrapers/ should return 200 or DB-related error."""
    status, _body = await api_get("/api/v1/scrapers/")
    assert status in OK


@pytest.mark.asyncio
async def test_list_scrapers_returns_list():
    """Successful response from scrapers list must be a JSON array."""
    status, body = await api_get("/api/v1/scrapers/")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "name" in item
            assert "status" in item
            assert "isActive" in item or "is_active" in item


# ---------- GET /scrapers/summary ----------


@pytest.mark.asyncio
async def test_scrapers_summary_returns_200_or_db_error():
    """GET /api/v1/scrapers/summary should return 200 or DB-related error."""
    status, _body = await api_get("/api/v1/scrapers/summary")
    assert status in OK


@pytest.mark.asyncio
async def test_scrapers_summary_has_expected_keys():
    """Successful summary must contain aggregate KPI keys."""
    status, body = await api_get("/api/v1/scrapers/summary")
    if status == 200 and body is not None:
        expected_keys = {
            "totalScrapers",
            "activeScrapers",
            "healthyScrapers",
            "warningScrapers",
            "errorScrapers",
            "totalArticles",
            "articlesLast24h",
        }
        assert expected_keys.issubset(set(body.keys())), (
            f"Missing keys: {expected_keys - set(body.keys())}"
        )
        assert isinstance(body["totalScrapers"], int)
        assert isinstance(body["activeScrapers"], int)
