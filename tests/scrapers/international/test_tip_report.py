"""Tests for the TIP Report scraper."""

import pytest

from data.scrapers.international.tip_report import TIPReportScraper


class TestTIPReportScraper:
    def test_init(self):
        scraper = TIPReportScraper()
        assert scraper.name == "tip_report"
        assert scraper.FIRST_YEAR == 2001

    def test_get_report_url(self):
        scraper = TIPReportScraper()
        url = scraper.get_report_url(2024)
        assert "2024" in url
        assert "pakistan" in url

    def test_extract_tier_ranking(self):
        scraper = TIPReportScraper()
        html = "<html><body><p>Pakistan is placed on Tier 2 Watch List.</p></body></html>"
        tier = scraper.extract_tier_ranking(html)
        assert tier == "Tier 2 Watch List"

    def test_extract_tier_ranking_tier2(self):
        scraper = TIPReportScraper()
        html = "<html><body><p>Tier 2</p></body></html>"
        tier = scraper.extract_tier_ranking(html)
        assert tier == "Tier 2"

    def test_extract_metrics(self):
        scraper = TIPReportScraper()
        html = """<html><body>
        <p>The government reported investigating 35 suspected trafficking cases,
        compared to 42 investigations the previous year.</p>
        <p>Authorities prosecuted 12 defendants and convicted 5 traffickers.</p>
        <p>The government identified 120 victims of trafficking.</p>
        </body></html>"""
        metrics = scraper.extract_metrics(html)
        assert metrics.get("investigations") == 35
        assert metrics.get("convictions") == 5

    def test_validate(self):
        scraper = TIPReportScraper()
        assert scraper.validate({"year": 2024, "tier_ranking": "Tier 2"})
        assert not scraper.validate({"year": 2024})
        assert not scraper.validate({"tier_ranking": "Tier 2"})
