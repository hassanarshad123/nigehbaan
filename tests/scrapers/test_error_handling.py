"""Error handling tests for the scraper base classes.

Validates retry logic, rate limiting, timeout handling, and response
parsing edge cases in BaseScraper, BaseAPIScraper, and BaseHTMLTableScraper.
Uses respx for HTTP mocking — no real network requests.
"""

from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from data.scrapers.base_api_scraper import BaseAPIScraper
from data.scrapers.base_html_scraper import BaseHTMLTableScraper
from data.scrapers.base_scraper import BaseScraper


# ─── Concrete test scraper implementations ────────────────────


class StubScraper(BaseScraper):
    """Minimal concrete scraper for testing BaseScraper methods."""

    name = "test_stub"
    source_url = "https://example.com"
    rate_limit_delay = 0.0  # No delay in tests
    request_timeout = 5.0
    max_retries = 3

    async def scrape(self) -> list[dict[str, Any]]:
        return []

    def validate(self, record: dict[str, Any]) -> bool:
        return bool(record.get("title"))


class StubAPIScraper(BaseAPIScraper):
    """Minimal concrete scraper for testing BaseAPIScraper methods."""

    name = "test_api_stub"
    source_url = "https://api.example.com"
    rate_limit_delay = 0.0
    request_timeout = 5.0
    max_retries = 3

    async def scrape(self) -> list[dict[str, Any]]:
        return []

    def validate(self, record: dict[str, Any]) -> bool:
        return bool(record.get("id"))


class StubHTMLScraper(BaseHTMLTableScraper):
    """Minimal concrete scraper for testing BaseHTMLTableScraper methods."""

    name = "test_html_stub"
    source_url = "https://html.example.com"
    rate_limit_delay = 0.0
    request_timeout = 5.0
    max_retries = 2

    async def scrape(self) -> list[dict[str, Any]]:
        return []

    def validate(self, record: dict[str, Any]) -> bool:
        return bool(record.get("name"))


# ═══════════════════════════════════════════════════════════════
# BaseScraper — retry and transport error handling
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_base_scraper_timeout_retries():
    """fetch() should retry on httpx.TimeoutException and raise after max_retries."""
    scraper = StubScraper()
    url = "https://example.com/slow"

    with respx.mock(assert_all_called=False) as router:
        # All attempts timeout
        route = router.get(url).mock(side_effect=httpx.TimeoutException("timed out"))

        with pytest.raises(httpx.TimeoutException):
            await scraper.fetch(url)

        # Should have been called max_retries times
        assert route.call_count == scraper.max_retries

    await scraper.close()


@pytest.mark.asyncio
async def test_base_scraper_connection_error():
    """fetch() should retry on httpx.ConnectError and raise after max_retries."""
    scraper = StubScraper()
    url = "https://example.com/down"

    with respx.mock(assert_all_called=False) as router:
        route = router.get(url).mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(httpx.ConnectError):
            await scraper.fetch(url)

        assert route.call_count == scraper.max_retries

    await scraper.close()


@pytest.mark.asyncio
async def test_base_scraper_http_500_retries():
    """fetch() should retry on HTTP 500 errors and raise after max_retries."""
    scraper = StubScraper()
    url = "https://example.com/error"

    with respx.mock(assert_all_called=False) as router:
        route = router.get(url).respond(500, text="Internal Server Error")

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await scraper.fetch(url)

        assert exc_info.value.response.status_code == 500
        assert route.call_count == scraper.max_retries

    await scraper.close()


@pytest.mark.asyncio
async def test_base_scraper_rate_limit_backoff():
    """fetch() should retry on HTTP 429 (rate limit) with exponential backoff."""
    scraper = StubScraper()
    url = "https://example.com/throttled"

    with respx.mock(assert_all_called=False) as router:
        route = router.get(url).respond(429, text="Too Many Requests")

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await scraper.fetch(url)

        assert exc_info.value.response.status_code == 429
        # All retries should have been attempted
        assert route.call_count == scraper.max_retries

    await scraper.close()


@pytest.mark.asyncio
async def test_base_scraper_empty_response():
    """fetch() should succeed on 200 with an empty body."""
    scraper = StubScraper()
    url = "https://example.com/empty"

    with respx.mock(assert_all_called=False) as router:
        router.get(url).respond(200, text="")

        response = await scraper.fetch(url)
        assert response.status_code == 200
        assert response.text == ""

    await scraper.close()


# ═══════════════════════════════════════════════════════════════
# BaseScraper — validation edge cases
# ═══════════════════════════════════════════════════════════════


def test_base_scraper_validate_empty_record():
    """validate({}) should return False for a stub scraper."""
    scraper = StubScraper()
    assert scraper.validate({}) is False


def test_base_scraper_validate_missing_required():
    """validate() with a partial record missing 'title' should return False."""
    scraper = StubScraper()
    record = {"url": "https://example.com", "body": "some text"}
    assert scraper.validate(record) is False


# ═══════════════════════════════════════════════════════════════
# BaseScraper — save_raw file creation
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_base_scraper_save_raw_creates_file(tmp_path: Path, monkeypatch):
    """save_raw() should create a JSON file in the raw data directory."""
    scraper = StubScraper()
    # Override RAW_DATA_DIR to use tmp_path
    monkeypatch.setattr(
        "data.scrapers.base_scraper.RAW_DATA_DIR", tmp_path / "raw"
    )

    data = [
        {"title": "Test article", "url": "https://example.com/1"},
        {"title": "Another article", "url": "https://example.com/2"},
    ]

    file_path = await scraper.save_raw(data)

    assert file_path.exists()
    assert file_path.suffix == ".json"
    assert file_path.parent.name == "test_stub"

    # Verify content is valid JSON with 2 records
    import json

    saved_data = json.loads(file_path.read_text(encoding="utf-8"))
    assert len(saved_data) == 2
    assert saved_data[0]["title"] == "Test article"


# ═══════════════════════════════════════════════════════════════
# BaseAPIScraper — JSON parsing edge cases
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_base_api_scraper_invalid_json():
    """fetch_json() should raise when the response is not valid JSON."""
    scraper = StubAPIScraper()
    url = "https://api.example.com/bad-json"

    with respx.mock(assert_all_called=False) as router:
        router.get(url).respond(
            200,
            text="<html>Not JSON</html>",
            headers={"Content-Type": "text/html"},
        )

        # response.json() should raise a JSONDecodeError
        with pytest.raises(Exception):
            await scraper.fetch_json(url)

    await scraper.close()


# ═══════════════════════════════════════════════════════════════
# BaseHTMLTableScraper — table extraction edge cases
# ═══════════════════════════════════════════════════════════════


def test_base_html_scraper_empty_table():
    """extract_tables() should skip tables with fewer than 2 rows (header only)."""
    scraper = StubHTMLScraper()

    html_with_empty_table = """<html><body>
    <table>
      <tr><th>Name</th><th>Age</th></tr>
    </table>
    </body></html>"""

    tables = scraper.extract_tables(html_with_empty_table)
    # A table with only a header row (1 row) should be skipped
    assert len(tables) == 0
