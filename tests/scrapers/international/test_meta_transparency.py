"""Tests for the Meta Transparency Report scraper."""

import pytest
import respx

from data.scrapers.international.meta_transparency import MetaTransparencyScraper


SAMPLE_META_HTML = """<html><body>
<h1>Community Standards Enforcement Report</h1>
<p>Q4 2024 Report</p>
<table>
  <tr>
    <th>Policy Area</th>
    <th>Content Actioned</th>
    <th>Proactive Rate</th>
  </tr>
  <tr>
    <td>Child nudity and sexual exploitation</td>
    <td>14.4M</td>
    <td>99.6%</td>
  </tr>
  <tr>
    <td>Hate Speech</td>
    <td>8.2M</td>
    <td>85.3%</td>
  </tr>
</table>
</body></html>"""

SAMPLE_META_SECTION_HTML = """<html><body>
<h2>Child Sexual Exploitation, Abuse and Nudity</h2>
<p>January 2024 - June 2024</p>
<table>
  <tr><th>Country</th><th>Reports</th><th>Content Removed</th></tr>
  <tr><td>Pakistan</td><td>1,250,000</td><td>98,500</td></tr>
  <tr><td>India</td><td>3,500,000</td><td>245,000</td></tr>
</table>
</body></html>"""


class TestMetaTransparencyScraper:
    def test_init(self):
        scraper = MetaTransparencyScraper()
        assert scraper.name == "meta_transparency"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = MetaTransparencyScraper()
        record = {
            "platform": "Meta",
            "metric": "test_metric",
            "report_period": "H1 2025",
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = MetaTransparencyScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_platform(self):
        scraper = MetaTransparencyScraper()
        record = {"metric": "test", "value": 100.0}
        assert scraper.validate(record) is False

    def test_validate_missing_metric(self):
        scraper = MetaTransparencyScraper()
        record = {"platform": "Meta", "value": 100.0}
        assert scraper.validate(record) is False

    def test_validate_none_value(self):
        scraper = MetaTransparencyScraper()
        record = {"platform": "Meta", "metric": "test", "value": None}
        assert scraper.validate(record) is False

    def test_parse_numeric(self):
        scraper = MetaTransparencyScraper()
        assert scraper._parse_numeric("14.4M") == 14_400_000.0
        assert scraper._parse_numeric("99.6%") == 99.6
        assert scraper._parse_numeric("450K") == 450_000.0
        assert scraper._parse_numeric("1,250,000") == 1250000.0
        assert scraper._parse_numeric("") is None

    def test_is_csam_related(self):
        scraper = MetaTransparencyScraper()
        assert scraper._is_csam_related(
            "Child nudity and sexual exploitation"
        ) is True
        assert scraper._is_csam_related("CSAM content removed") is True
        assert scraper._is_csam_related("Hate Speech policy") is False

    def test_extract_period(self):
        scraper = MetaTransparencyScraper()
        assert scraper._extract_period("Q4 2024 Report") == "Q4 2024"
        assert scraper._extract_period(
            "January 2024 - June 2024"
        ) == "January 2024 - June 2024"

    def test_infer_unit(self):
        scraper = MetaTransparencyScraper()
        assert scraper._infer_unit("proactive rate", "99.6%") == "percent"
        assert scraper._infer_unit("content actioned", "14.4M") == "content_pieces"
        assert scraper._infer_unit("appeals", "1000") == "appeals"

    def test_build_section_urls(self):
        scraper = MetaTransparencyScraper()
        urls = scraper._build_section_urls()
        assert len(urls) > 0
        assert all("child" in url for url in urls)

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get(url__regex=r".*transparency\.meta\.com.*").respond(
            200, text=SAMPLE_META_HTML
        )
        scraper = MetaTransparencyScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
