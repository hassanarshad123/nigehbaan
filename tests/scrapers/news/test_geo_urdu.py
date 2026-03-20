"""Tests for the Geo Urdu news scraper."""

import pytest
import respx

from data.scrapers.news.geo_urdu import GeoUrduScraper


MOCK_LISTING_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head><meta charset="UTF-8"><title>Geo Urdu - Latest News</title></head>
<body>
<div class="news-list">
  <h2><a href="https://urdu.geo.tv/latest/12345">لاہور میں بچوں کی سمگلنگ کا واقعہ</a></h2>
  <h2><a href="https://urdu.geo.tv/latest/67890">موسم کی تازہ صورتحال</a></h2>
  <h2><a href="https://urdu.geo.tv/latest/11111">فیصل آباد میں بچوں سے زیادتی</a></h2>
</div>
</body></html>"""

MOCK_ARTICLE_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head>
  <meta charset="UTF-8">
  <title>لاہور میں بچوں کی سمگلنگ کا واقعہ</title>
  <meta property="article:published_time" content="2026-03-20T10:00:00+05:00">
</head>
<body>
<article>
  <h1>لاہور میں بچوں کی سمگلنگ کا واقعہ</h1>
  <span class="story-date">20 مارچ 2026</span>
  <span class="story-author">جیو نیوز</span>
  <div class="story-detail">
    <p>لاہور: پولیس نے بچوں کی سمگلنگ کے الزام میں پانچ ملزمان کو گرفتار کر لیا۔</p>
    <p>ایف آئی اے نے چھاپے میں تین بچوں کو بازیاب کرایا جن کی عمریں آٹھ سے بارہ سال تھیں۔</p>
  </div>
</article>
</body></html>"""


class TestGeoUrduScraper:
    def test_init(self):
        scraper = GeoUrduScraper()
        assert scraper.name == "geo_urdu"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = GeoUrduScraper()
        record = {
            "url": "https://example.com/article",
            "title": "Test Title",
            "published_date": "2026-01-01",
            "full_text": "Test body.",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = GeoUrduScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_title(self):
        scraper = GeoUrduScraper()
        record = {"url": "https://example.com", "full_text": "body"}
        assert scraper.validate(record) is False

    def test_validate_missing_url(self):
        scraper = GeoUrduScraper()
        record = {"title": "Test", "full_text": "body"}
        assert scraper.validate(record) is False

    def test_validate_missing_full_text(self):
        scraper = GeoUrduScraper()
        record = {"url": "https://example.com", "title": "Test"}
        assert scraper.validate(record) is False

    def test_matches_urdu_keywords(self, monkeypatch):
        scraper = GeoUrduScraper()
        monkeypatch.setattr(scraper, "urdu_keywords", ["سمگلنگ", "اغوا"])
        assert scraper._matches_urdu_keywords("بچوں کی سمگلنگ") is True
        assert scraper._matches_urdu_keywords("کھیلوں کی خبریں") is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        listing_url = "https://urdu.geo.tv/latest-news"
        respx.get(listing_url).respond(200, text=MOCK_LISTING_HTML)
        respx.get(url__regex=r".*urdu\.geo\.tv/latest/.*").respond(
            200, text=MOCK_ARTICLE_HTML
        )

        scraper = GeoUrduScraper()
        scraper.rate_limit_delay = 0
        monkeypatch.setattr(scraper, "urdu_keywords", ["سمگلنگ", "زیادتی"])
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
