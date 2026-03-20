"""Tests for the RSS monitor scraper."""

import pytest
import respx

from data.scrapers.news.rss_monitor import RSSMonitor


class TestRSSMonitor:
    def test_init_default_feeds(self):
        monitor = RSSMonitor()
        assert "google_news_trafficking" in monitor.feeds
        assert "dawn" in monitor.feeds
        assert len(monitor.feeds) > 0

    def test_init_custom_feeds(self):
        custom = {"test": "https://example.com/rss"}
        monitor = RSSMonitor(feeds=custom)
        assert monitor.feeds == custom

    def test_normalize_url(self):
        monitor = RSSMonitor()
        # Strip trailing slashes
        assert monitor.normalize_url("https://example.com/article/") == "https://example.com/article"
        # Strip UTM params
        normalized = monitor.normalize_url("https://example.com/article?utm_source=rss&utm_medium=feed")
        assert "utm_source" not in normalized

    def test_validate(self):
        monitor = RSSMonitor()
        assert monitor.validate({"url": "http://example.com", "title": "Test"})
        assert not monitor.validate({"url": "http://example.com"})
        assert not monitor.validate({"title": "Test"})
        assert not monitor.validate({})

    def test_deduplicate(self):
        monitor = RSSMonitor()
        entries = [
            {"url": "https://example.com/1", "title": "Article 1"},
            {"url": "https://example.com/1", "title": "Article 1 (dup)"},
            {"url": "https://example.com/2", "title": "Article 2"},
        ]
        deduped = monitor.deduplicate(entries)
        assert len(deduped) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_feed(self, sample_rss_xml):
        respx.get("https://example.com/rss").respond(200, text=sample_rss_xml)
        monitor = RSSMonitor()
        monitor.rate_limit_delay = 0
        entries = await monitor.fetch_feed("test", "https://example.com/rss")
        assert len(entries) > 0
        await monitor.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape_returns_articles(self, sample_rss_xml):
        # Mock all feeds
        respx.get(url__regex=r".*").respond(200, text=sample_rss_xml)
        monitor = RSSMonitor(feeds={"test": "https://example.com/rss"})
        monitor.rate_limit_delay = 0
        results = await monitor.scrape()
        assert isinstance(results, list)
        await monitor.close()
