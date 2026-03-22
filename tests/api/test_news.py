"""Tests for the /api/v1/news/* endpoints.

News endpoints query the news_articles table. When the DB is unavailable
the asyncpg driver raises before FastAPI can respond, so the shared
``api_get`` helper converts that into a synthetic 503.
"""

import pytest

from tests.api.conftest import ACCEPTABLE_CODES_WITH_DB_DOWN, api_get

OK = ACCEPTABLE_CODES_WITH_DB_DOWN


# ---------- GET /news/ ----------


@pytest.mark.asyncio
async def test_list_news_returns_200_or_db_error():
    """GET /api/v1/news/ should return 200 or a DB-related error."""
    status, _body = await api_get("/api/v1/news/")
    assert status in OK


@pytest.mark.asyncio
async def test_list_news_returns_list():
    """Successful response must be a list of news article items."""
    status, body = await api_get("/api/v1/news/")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        if len(body) > 0:
            item = body[0]
            assert "id" in item
            assert "title" in item
            assert "sourceName" in item


@pytest.mark.asyncio
async def test_list_news_pagination():
    """Pagination should limit the number of results."""
    status, body = await api_get("/api/v1/news/", page=1, limit=5)
    if status == 200 and body is not None:
        assert isinstance(body, list)
        assert len(body) <= 5


@pytest.mark.asyncio
async def test_list_news_filter_source():
    """Filtering by source_name should return only matching articles."""
    status, body = await api_get("/api/v1/news/", source_name="dawn")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        for item in body:
            assert item["sourceName"] == "dawn"


@pytest.mark.asyncio
async def test_list_news_filter_date_range():
    """Filtering by date_from should return articles from that date onward."""
    status, body = await api_get("/api/v1/news/", date_from="2024-01-01")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        for item in body:
            if item.get("publishedDate"):
                assert item["publishedDate"] >= "2024-01-01"


@pytest.mark.asyncio
async def test_list_news_filter_relevant():
    """Filtering by is_trafficking_relevant=true should return only relevant articles."""
    status, body = await api_get("/api/v1/news/", is_trafficking_relevant="true")
    if status == 200 and body is not None:
        assert isinstance(body, list)
        for item in body:
            assert item.get("isTraffickingRelevant") is True


@pytest.mark.asyncio
async def test_list_news_response_schema():
    """Each list item must have the expected schema keys."""
    status, body = await api_get("/api/v1/news/")
    if status == 200 and body is not None and len(body) > 0:
        item = body[0]
        expected_keys = {"id", "title", "sourceName", "publishedDate", "snippet"}
        assert expected_keys.issubset(set(item.keys())), (
            f"Missing keys: {expected_keys - set(item.keys())}"
        )


@pytest.mark.asyncio
async def test_list_news_snippet_truncated():
    """Snippet should be at most 200 characters (+ ellipsis)."""
    status, body = await api_get("/api/v1/news/")
    if status == 200 and body is not None:
        for item in body:
            snippet = item.get("snippet")
            if snippet is not None:
                assert len(snippet) <= 204  # 200 + "..."


# ---------- GET /news/{id} ----------


@pytest.mark.asyncio
async def test_get_news_detail_not_found():
    """GET /api/v1/news/99999 should return 404."""
    status, body = await api_get("/api/v1/news/99999")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 404


@pytest.mark.asyncio
async def test_get_news_detail_schema():
    """If articles exist, detail should include full_text and extracted data."""
    # First get a list to find an article ID
    list_status, list_body = await api_get("/api/v1/news/", limit=1)
    if list_status != 200 or not list_body or len(list_body) == 0:
        pytest.skip("No articles available or DB unavailable")

    article_id = list_body[0]["id"]
    status, body = await api_get(f"/api/v1/news/{article_id}")
    if status == 503:
        pytest.skip("DB unavailable")
    assert status == 200
    assert body is not None
    assert body["id"] == article_id
    assert "fullText" in body
    assert "url" in body
    assert "createdAt" in body
