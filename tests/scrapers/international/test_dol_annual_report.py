"""Tests for the DOL Annual Report scraper."""

import pytest
import respx

from data.scrapers.international.dol_annual_report import DOLAnnualReportScraper


MOCK_CATALOG_HTML = """<html><body>
<h1>Findings on the Worst Forms of Child Labor - Pakistan</h1>
<ul>
  <li><a href="/sites/dolgov/files/ILAB/pakistan_2023.pdf">Pakistan 2023 Findings</a></li>
  <li><a href="/sites/dolgov/files/ILAB/pakistan_2022.pdf">Pakistan 2022 Findings</a></li>
</ul>
</body></html>"""


class TestDOLAnnualReportScraper:
    def test_init(self):
        scraper = DOLAnnualReportScraper()
        assert scraper.name == "dol_annual_report"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = DOLAnnualReportScraper()
        record = {
            "source_name": "dol_annual_report",
            "indicator": "child_labor_rate",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = DOLAnnualReportScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_year(self):
        scraper = DOLAnnualReportScraper()
        record = {"source_name": "dol_annual_report", "indicator": "test"}
        assert scraper.validate(record) is False

    def test_extract_year(self):
        assert DOLAnnualReportScraper._extract_year("pakistan_2023.pdf") == "2023"
        assert DOLAnnualReportScraper._extract_year("report_2021_v2.pdf") == "2021"

    def test_parse_numeric(self):
        assert DOLAnnualReportScraper._parse_numeric("1,234") == 1234.0
        assert DOLAnnualReportScraper._parse_numeric("") is None
        assert DOLAnnualReportScraper._parse_numeric("abc") is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, sample_pdf_bytes, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        catalog_url = (
            "https://www.dol.gov/agencies/ilab/resources/reports/"
            "child-labor/pakistan"
        )
        respx.get(catalog_url).respond(200, text=MOCK_CATALOG_HTML)
        respx.get(url__regex=r".*\.pdf$").respond(
            200,
            content=sample_pdf_bytes,
            headers={"Content-Type": "application/pdf"},
        )

        scraper = DOLAnnualReportScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
