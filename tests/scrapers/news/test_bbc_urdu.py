"""Tests for the BBC Urdu news scraper."""

import pytest
import respx

from data.scrapers.news.bbc_urdu import BBCUrduScraper


MOCK_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>BBC Urdu</title>
    <link>https://www.bbc.com/urdu</link>
    <item>
      <title>لاہور میں بچوں کی سمگلنگ کا انکشاف</title>
      <link>https://www.bbc.com/urdu/articles/test-article-1</link>
      <pubDate>Thu, 20 Mar 2026 10:00:00 +0500</pubDate>
      <description>ایف آئی اے نے بچوں کی سمگلنگ کے نیٹ ورک کا پردہ فاش کیا</description>
    </item>
    <item>
      <title>کراچی میں بارش کا امکان</title>
      <link>https://www.bbc.com/urdu/articles/test-article-2</link>
      <pubDate>Thu, 20 Mar 2026 11:00:00 +0500</pubDate>
      <description>محکمہ موسمیات نے بارش کی پیشگوئی کی ہے</description>
    </item>
    <item>
      <title>پنجاب میں بچوں سے زیادتی کے خلاف مہم</title>
      <link>https://www.bbc.com/urdu/articles/test-article-3</link>
      <pubDate>Thu, 20 Mar 2026 12:00:00 +0500</pubDate>
      <description>حکومت نے بچوں کے تحفظ کے لیے نئی مہم شروع کی</description>
    </item>
  </channel>
</rss>"""

MOCK_ARTICLE_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head>
  <meta charset="UTF-8">
  <title>لاہور میں بچوں کی سمگلنگ کا انکشاف</title>
  <meta property="article:published_time" content="2026-03-20T10:00:00+05:00">
</head>
<body>
<main role="main">
  <h1>لاہور میں بچوں کی سمگلنگ کا انکشاف</h1>
  <div class="byline">بی بی سی اردو</div>
  <time datetime="2026-03-20">20 مارچ 2026</time>
  <p>لاہور: ایف آئی اے نے بچوں کی سمگلنگ میں ملوث ایک بین الاقوامی نیٹ ورک کا پردہ فاش کیا ہے۔</p>
  <p>حکام کے مطابق پانچ ملزمان کو گرفتار کیا گیا ہے جو بچوں کو بیرون ملک اسمگل کرتے تھے۔</p>
  <p>تین بچے جن کی عمریں آٹھ سے بارہ سال کے درمیان ہیں، بازیاب کرائے گئے۔</p>
</main>
</body></html>"""


class TestBBCUrduScraper:
    def test_init(self):
        scraper = BBCUrduScraper()
        assert scraper.name == "bbc_urdu"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = BBCUrduScraper()
        record = {
            "url": "https://example.com/article",
            "title": "Test Title",
            "published_date": "2026-01-01",
            "full_text": "Test body.",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = BBCUrduScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_title(self):
        scraper = BBCUrduScraper()
        record = {"url": "https://example.com", "full_text": "body"}
        assert scraper.validate(record) is False

    def test_validate_missing_url(self):
        scraper = BBCUrduScraper()
        record = {"title": "Test", "full_text": "body"}
        assert scraper.validate(record) is False

    def test_validate_missing_full_text(self):
        scraper = BBCUrduScraper()
        record = {"url": "https://example.com", "title": "Test"}
        assert scraper.validate(record) is False

    def test_matches_urdu_keywords(self, monkeypatch):
        scraper = BBCUrduScraper()
        monkeypatch.setattr(scraper, "urdu_keywords", ["سمگلنگ", "اغوا"])
        assert scraper._matches_urdu_keywords("بچوں کی سمگلنگ") is True
        assert scraper._matches_urdu_keywords("کھیلوں کی خبریں") is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_rss(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        rss_url = "https://feeds.bbci.co.uk/urdu/rss.xml"
        respx.get(rss_url).respond(200, text=MOCK_RSS_FEED)

        scraper = BBCUrduScraper()
        scraper.rate_limit_delay = 0
        entries = await scraper.fetch_rss()
        assert isinstance(entries, list)
        assert len(entries) == 3
        assert entries[0]["title"]
        assert entries[0]["url"]
        await scraper.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        rss_url = "https://feeds.bbci.co.uk/urdu/rss.xml"
        respx.get(rss_url).respond(200, text=MOCK_RSS_FEED)
        respx.get(url__regex=r".*bbc\.com/urdu.*").respond(
            200, text=MOCK_ARTICLE_HTML
        )

        scraper = BBCUrduScraper()
        scraper.rate_limit_delay = 0
        monkeypatch.setattr(scraper, "urdu_keywords", ["سمگلنگ", "زیادتی"])
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
