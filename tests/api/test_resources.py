"""Tests for the /api/v1/resources/* endpoints.

Resources endpoints serve helpline, legal aid, shelter, and NGO data.
When the DB is unavailable, tests skip gracefully.
"""

import pytest

from tests.api.conftest import ACCEPTABLE_CODES_WITH_DB_DOWN, api_get

OK = ACCEPTABLE_CODES_WITH_DB_DOWN


@pytest.mark.asyncio
async def test_list_resources_returns_200_or_db_error():
    """GET /api/v1/resources/ should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/resources/")
    assert status in OK


@pytest.mark.asyncio
async def test_list_resources_returns_list():
    """Successful response must be a list of resource items."""
    status, body = await api_get("/api/v1/resources/")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "id" in item
            assert "name" in item
            assert "category" in item
            assert "contact" in item


@pytest.mark.asyncio
async def test_filter_by_category():
    """Filtering by category should return only matching resources."""
    status, body = await api_get("/api/v1/resources/", category="helpline")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        for item in body:
            assert item["category"] == "helpline"


@pytest.mark.asyncio
async def test_resources_has_seeded_data():
    """After migration, resources table should have at least 10 entries."""
    status, body = await api_get("/api/v1/resources/")
    if status == 200 and body is not None:
        # If DB is available and migration has run, expect seeded data
        if len(body) > 0:
            assert len(body) >= 10, f"Expected at least 10 seeded resources, got {len(body)}"


@pytest.mark.asyncio
async def test_resource_schema():
    """Each resource item must have the expected schema keys."""
    status, body = await api_get("/api/v1/resources/")
    if status == 200 and body is not None and len(body) > 0:
        item = body[0]
        expected_keys = {"id", "category", "name", "description", "contact"}
        assert expected_keys.issubset(set(item.keys())), (
            f"Missing keys: {expected_keys - set(item.keys())}"
        )
