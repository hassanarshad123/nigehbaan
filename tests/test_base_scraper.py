"""Tests for the base scraper infrastructure."""

import json
from typing import Any

import pytest
import httpx
import respx

from data.scrapers.base_scraper import BaseScraper


# Concrete implementation for testing
class MockScraper(BaseScraper):
    name = "test_scraper"
    source_url = "https://example.com"
    schedule = "0 */6 * * *"
    priority = "P1"

    def __init__(self, data: list[dict] | None = None):
        super().__init__()
        self._data = data or []

    async def scrape(self) -> list[dict[str, Any]]:
        return self._data

    def validate(self, record: dict[str, Any]) -> bool:
        return bool(record.get("title"))


class TestBaseScraper:
    def test_init(self):
        scraper = MockScraper()
        assert scraper.name == "test_scraper"
        assert scraper.run_id is not None
        assert scraper._client is None

    @pytest.mark.asyncio
    async def test_get_client(self):
        scraper = MockScraper()
        client = await scraper.get_client()
        assert isinstance(client, httpx.AsyncClient)
        assert not client.is_closed
        await scraper.close()

    @pytest.mark.asyncio
    async def test_close(self):
        scraper = MockScraper()
        await scraper.get_client()
        await scraper.close()
        assert scraper._client is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_success(self):
        respx.get("https://example.com/test").respond(200, text="OK")
        scraper = MockScraper()
        scraper.rate_limit_delay = 0  # Speed up tests
        response = await scraper.fetch("https://example.com/test")
        assert response.status_code == 200
        assert response.text == "OK"
        await scraper.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_retry_on_failure(self):
        route = respx.get("https://example.com/retry")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, text="success"),
        ]
        scraper = MockScraper()
        scraper.rate_limit_delay = 0
        scraper.max_retries = 2
        response = await scraper.fetch("https://example.com/retry")
        assert response.text == "success"
        await scraper.close()

    def test_matches_keywords(self):
        scraper = MockScraper()
        assert scraper.matches_keywords("child trafficking ring busted")
        assert scraper.matches_keywords("FIA arrests suspects")
        assert scraper.matches_keywords("Section 366-A PPC")
        assert not scraper.matches_keywords("weather forecast for Karachi")
        assert not scraper.matches_keywords("cricket match results")

    def test_matches_keywords_case_insensitive(self):
        scraper = MockScraper()
        assert scraper.matches_keywords("CHILD TRAFFICKING in Pakistan")
        assert scraper.matches_keywords("Human Trafficking")

    def test_validate(self):
        scraper = MockScraper()
        assert scraper.validate({"title": "test"})
        assert not scraper.validate({"url": "http://example.com"})
        assert not scraper.validate({})

    @pytest.mark.asyncio
    async def test_save_raw_json(self, tmp_path):
        scraper = MockScraper()
        # Override the raw data dir
        scraper.get_raw_dir = lambda: tmp_path / "test_scraper"
        (tmp_path / "test_scraper").mkdir(parents=True)

        data = [{"title": "Article 1", "url": "http://example.com/1"}]
        path = await scraper.save_raw(data, "json")
        assert path.exists()
        loaded = json.loads(path.read_text())
        assert len(loaded) == 1
        assert loaded[0]["title"] == "Article 1"

    @pytest.mark.asyncio
    async def test_run_pipeline(self, tmp_path):
        data = [
            {"title": "Good article", "url": "http://example.com/1"},
            {"url": "http://example.com/2"},  # Missing title, should be filtered
        ]
        scraper = MockScraper(data=data)
        scraper.get_raw_dir = lambda: tmp_path / "test_scraper"
        (tmp_path / "test_scraper").mkdir(parents=True)

        results = await scraper.run()
        assert len(results) == 1
        assert results[0]["title"] == "Good article"


class TestBaseCourtScraper:
    def test_extract_ppc_sections(self):
        from data.scrapers.courts.base_court_scraper import extract_ppc_sections
        text = "convicted under section 370 and 371-A PPC read with section 366-A"
        sections = extract_ppc_sections(text)
        assert "370" in sections
        assert "371-A" in sections
        assert "366-A" in sections

    def test_normalize_ppc_section(self):
        from data.scrapers.courts.base_court_scraper import normalize_ppc_section
        assert normalize_ppc_section("366A") == "366-A"
        assert normalize_ppc_section("371-a") == "371-A"
        assert normalize_ppc_section("370") == "370"

    def test_parse_pakistani_date(self):
        from data.scrapers.courts.base_court_scraper import parse_pakistani_date
        d = parse_pakistani_date("15-01-2024")
        assert d is not None
        assert d.day == 15
        assert d.month == 1
        assert d.year == 2024

        d2 = parse_pakistani_date("January 15, 2024")
        assert d2 is not None
        assert d2.year == 2024

    def test_filter_relevant_sections(self):
        from data.scrapers.courts.base_court_scraper import filter_relevant_sections
        sections = ["370", "302", "366-A", "420"]
        relevant = filter_relevant_sections(sections)
        assert "370" in relevant
        assert "366-A" in relevant
        assert "302" not in relevant
        assert "420" not in relevant
