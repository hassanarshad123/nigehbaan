"""Tests for the Jang Urdu news scraper."""

import pytest
import respx

from data.scrapers.news.jang_urdu import JangUrduScraper


MOCK_LISTING_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head><meta charset="UTF-8"><title>Daily Jang - Latest News</title></head>
<body>
<div class="news-list">
  <h2><a href="/news-12345">لاہور میں بچوں کی سمگلنگ کا واقعہ</a></h2>
  <h2><a href="/news-67890">کراچی میں موسم کی صورتحال</a></h2>
  <h2><a href="/news-11111">اسلام آباد میں بچوں سے زیادتی</a></h2>
</div>
</body></html>"""

MOCK_ARTICLE_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head><meta charset="UTF-8"><title>لاہور میں بچوں کی سمگلنگ کا واقعہ</title></head>
<body>
<article>
  <h1>لاہور میں بچوں کی سمگلنگ کا واقعہ</h1>
  <span class="date">20 مارچ 2026</span>
  <div class="detail-content">
    <p>لاہور: پولیس نے بچوں کی سمگلنگ کے الزام میں پانچ ملزمان کو گرفتار کر لیا۔</p>
    <p>ایف آئی اے کی ٹیم نے متعدد مقامات پر چھاپے مارے۔ ملزمان بچوں کی اسمگلنگ میں ملوث تھے۔</p>
  </div>
</article>
</body></html>"""


class TestJangUrduScraper:
    def test_init(self):
        scraper = JangUrduScraper()
        assert scraper.name == "jang_urdu"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = JangUrduScraper()
        record = {
            "url": "https://example.com/article",
            "title": "Test Title",
            "published_date": "2026-01-01",
            "full_text": "Test body.",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = JangUrduScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_title(self):
        scraper = JangUrduScraper()
        record = {"url": "https://example.com", "full_text": "body"}
        assert scraper.validate(record) is False

    def test_validate_missing_url(self):
        scraper = JangUrduScraper()
        record = {"title": "Test", "full_text": "body"}
        assert scraper.validate(record) is False

    def test_validate_missing_full_text(self):
        scraper = JangUrduScraper()
        record = {"url": "https://example.com", "title": "Test"}
        assert scraper.validate(record) is False

    def test_matches_urdu_keywords(self, monkeypatch):
        scraper = JangUrduScraper()
        # Inject test keywords directly
        monkeypatch.setattr(scraper, "urdu_keywords", ["سمگلنگ", "اغوا"])
        assert scraper._matches_urdu_keywords("بچوں کی سمگلنگ") is True
        assert scraper._matches_urdu_keywords("موسم کی خبر") is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        listing_url = "https://jang.com.pk/latest-news"
        respx.get(listing_url).respond(200, text=MOCK_LISTING_HTML)
        respx.get(url__regex=r".*jang\.com\.pk/news-.*").respond(
            200, text=MOCK_ARTICLE_HTML
        )

        scraper = JangUrduScraper()
        scraper.rate_limit_delay = 0
        # Inject a keyword that matches the mock content
        monkeypatch.setattr(scraper, "urdu_keywords", ["سمگلنگ", "زیادتی"])
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
