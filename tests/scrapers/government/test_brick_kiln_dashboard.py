"""Tests for the Brick Kiln Dashboard scraper."""

import pytest
import respx

from data.scrapers.government.brick_kiln_dashboard import BrickKilnDashboardScraper


MOCK_DASHBOARD_HTML = """<html><body>
<h1>Brick Kiln Monitoring Dashboard</h1>
<div class="counter">10,234 Kilns</div>
<div class="counter">126,000 Children</div>
<div class="counter">36 Districts</div>
<div class="stat">85,000 Workers</div>
<script>
  fetch("/api/data").then(r => r.json());
</script>
</body></html>"""

MOCK_API_JSON = {
    "total_kilns": 10234,
    "total_children": 126000,
    "total_districts": 36,
    "total_workers": 85000,
    "school_enrollment": 42000,
}


class TestBrickKilnDashboardScraper:
    def test_init(self):
        scraper = BrickKilnDashboardScraper()
        assert scraper.name == "brick_kiln_dashboard"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = BrickKilnDashboardScraper()
        record = {
            "source_name": "brick_kiln_dashboard",
            "indicator": "total_kilns",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = BrickKilnDashboardScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_value(self):
        scraper = BrickKilnDashboardScraper()
        record = {"source_name": "brick_kiln_dashboard", "indicator": "total_kilns"}
        assert scraper.validate(record) is False

    def test_validate_missing_indicator(self):
        scraper = BrickKilnDashboardScraper()
        record = {"source_name": "brick_kiln_dashboard", "value": 100}
        assert scraper.validate(record) is False

    def test_summarize_list(self):
        data = [
            {"district": "Lahore", "children": "500"},
            {"district": "Faisalabad", "children": "300"},
            {"district": "Lahore", "children": "200"},
        ]
        summary = BrickKilnDashboardScraper._summarize_list(data)
        assert summary["total_records"] == 3
        assert summary["unique_districts"] == 2
        assert summary["total_children"] == 1000

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape_with_api(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        base_url = "https://dashboards.urbanunit.gov.pk/brick_kilns/"
        respx.get(base_url).respond(200, text=MOCK_DASHBOARD_HTML)
        respx.get(url__regex=r".*api.*").respond(
            200,
            json=MOCK_API_JSON,
            headers={"Content-Type": "application/json"},
        )
        # Let other probed URLs return 404
        respx.route().respond(404)

        scraper = BrickKilnDashboardScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape_html_fallback(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        base_url = "https://dashboards.urbanunit.gov.pk/brick_kilns/"
        respx.get(url__regex=r".*").respond(200, text=MOCK_DASHBOARD_HTML)

        scraper = BrickKilnDashboardScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
