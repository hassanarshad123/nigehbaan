"""Tests for the Express Urdu news scraper."""

import pytest
import respx

from data.scrapers.news.express_urdu import ExpressUrduScraper


MOCK_LISTING_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head><meta charset="UTF-8"><title>Express Urdu - Latest News</title></head>
<body>
<div class="listing-page">
  <h2><a href="https://www.express.pk/story/2345678">لاہور میں بچوں کی سمگلنگ</a></h2>
  <h2><a href="https://www.express.pk/story/2345679">کراچی کی خبریں</a></h2>
  <h2><a href="https://www.express.pk/story/2345680">بچوں سے زیادتی کا واقعہ</a></h2>
</div>
</body></html>"""

MOCK_ARTICLE_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head>
  <meta charset="UTF-8">
  <title>لاہور میں بچوں کی سمگلنگ</title>
  <meta property="article:published_time" content="2026-03-20T10:00:00+05:00">
</head>
<body>
<article>
  <h1 class="entry-title">لاہور میں بچوں کی سمگلنگ</h1>
  <div class="entry-content">
    <p>لاہور: ایف آئی اے نے بچوں کی سمگلنگ میں ملوث پانچ افراد کو گرفتار کر لیا۔</p>
    <p>ملزمان نے اعتراف جرم کیا کہ وہ بچوں کی اسمگلنگ کے کاروبار میں ملوث تھے۔</p>
  </div>
</article>
</body></html>"""


class TestExpressUrduScraper:
    def test_init(self):
        scraper = ExpressUrduScraper()
        assert scraper.name == "express_urdu"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = ExpressUrduScraper()
        record = {
            "url": "https://example.com/article",
            "title": "Test Title",
            "published_date": "2026-01-01",
            "full_text": "Test body.",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = ExpressUrduScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_title(self):
        scraper = ExpressUrduScraper()
        record = {"url": "https://example.com", "full_text": "body"}
        assert scraper.validate(record) is False

    def test_validate_missing_url(self):
        scraper = ExpressUrduScraper()
        record = {"title": "Test", "full_text": "body"}
        assert scraper.validate(record) is False

    def test_validate_missing_full_text(self):
        scraper = ExpressUrduScraper()
        record = {"url": "https://example.com", "title": "Test"}
        assert scraper.validate(record) is False

    def test_matches_urdu_keywords(self, monkeypatch):
        scraper = ExpressUrduScraper()
        monkeypatch.setattr(scraper, "urdu_keywords", ["سمگلنگ", "اغوا"])
        assert scraper._matches_urdu_keywords("بچوں کی سمگلنگ") is True
        assert scraper._matches_urdu_keywords("کھیل کی خبر") is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        listing_url = "https://www.express.pk/latest-news/"
        respx.get(listing_url).respond(200, text=MOCK_LISTING_HTML)
        respx.get(url__regex=r".*express\.pk/story/.*").respond(
            200, text=MOCK_ARTICLE_HTML
        )

        scraper = ExpressUrduScraper()
        scraper.rate_limit_delay = 0
        monkeypatch.setattr(scraper, "urdu_keywords", ["سمگلنگ", "زیادتی"])
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
