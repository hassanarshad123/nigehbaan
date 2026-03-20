"""Tests for the Brookings Bride scraper."""

import pytest
import respx

from data.scrapers.international.brookings_bride import BrookingsBrideScraper


MOCK_ARTICLE_HTML = """<html><body>
<h1>629 Pakistani Girls Sold as Brides to Chinese Men</h1>
<div class="author"><a class="author-link">Nida Kirmani</a></div>
<time datetime="2019-12-04">December 4, 2019</time>
<div class="post-body">
  <p>An investigation has uncovered that 629 Pakistani girls and women were
  sold as brides to Chinese men between 2018 and 2019.</p>
  <p>The victims were aged 13 to 25, and many were from impoverished
  Christian communities in Punjab province.</p>
  <p>Pakistani authorities filed 52 FIRs against suspects involved in
  the trafficking ring.</p>
</div>
</body></html>"""


class TestBrookingsBrideScraper:
    def test_init(self):
        scraper = BrookingsBrideScraper()
        assert scraper.name == "brookings_bride"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = BrookingsBrideScraper()
        record = {
            "source_name": "Brookings Institution",
            "indicator": "cross_border_bride_trafficking",
            "report_title": "Pakistani Brides Sold to Chinese Men",
            "value": 629,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = BrookingsBrideScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_source(self):
        scraper = BrookingsBrideScraper()
        record = {"indicator": "test", "report_title": "Test"}
        assert scraper.validate(record) is False

    def test_validate_no_indicator_or_title(self):
        scraper = BrookingsBrideScraper()
        record = {"source_name": "Brookings Institution"}
        assert scraper.validate(record) is False

    def test_extract_article_stats(self):
        scraper = BrookingsBrideScraper()
        records = scraper._extract_article_stats(MOCK_ARTICLE_HTML)
        assert isinstance(records, list)
        assert len(records) >= 1
        # Base record should have 629 victims
        base = records[0]
        assert base["value"] == 629
        assert base["source_name"] == "Brookings Institution"

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        article_url = "https://www.brookings.edu/articles/pakistani-brides/"
        respx.get(article_url).respond(200, text=MOCK_ARTICLE_HTML)

        scraper = BrookingsBrideScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        assert len(results) >= 1
        await scraper.close()
