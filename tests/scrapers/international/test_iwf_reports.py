"""Tests for the IWF (Internet Watch Foundation) annual report scraper."""

import pytest
import respx

from data.scrapers.international.iwf_reports import IWFReportsScraper


SAMPLE_IWF_HTML = """<html><body>
<h1>IWF Annual Reports</h1>
<p>In 2023, the IWF assessed over 375,000 reports and confirmed
275,655 URLs containing child sexual abuse imagery.</p>
<ul>
  <li><a href="https://www.iwf.org.uk/media/annual-report-2023.pdf">
    Annual Report 2023</a></li>
  <li><a href="https://www.iwf.org.uk/media/annual-report-2022.pdf">
    Annual Report 2022</a></li>
</ul>
</body></html>"""


class TestIWFReportsScraper:
    def test_init(self):
        scraper = IWFReportsScraper()
        assert scraper.name == "iwf_reports"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = IWFReportsScraper()
        record = {
            "source_name": "iwf_reports",
            "indicator": "test_indicator",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_with_report_title(self):
        scraper = IWFReportsScraper()
        record = {
            "source_name": "IWF",
            "indicator": "Confirmed CSAM URLs",
            "report_title": "IWF Annual Report",
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = IWFReportsScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_indicator(self):
        scraper = IWFReportsScraper()
        record = {"source_name": "IWF"}
        assert scraper.validate(record) is False

    def test_extract_year(self):
        scraper = IWFReportsScraper()
        assert scraper._extract_year(
            "https://www.iwf.org.uk/media/annual-report-2023.pdf"
        ) == 2023
        assert scraper._extract_year("no year") is None

    def test_parse_numeric(self):
        scraper = IWFReportsScraper()
        assert scraper._parse_numeric("275,655") == 275655.0
        assert scraper._parse_numeric("45.6%") == 45.6
        assert scraper._parse_numeric("") is None

    def test_infer_unit(self):
        assert IWFReportsScraper._infer_unit("Confirmed URLs", "275,655") == "URLs"
        assert IWFReportsScraper._infer_unit("Reports Assessed", "375,000") == "reports"
        assert IWFReportsScraper._infer_unit("Hashes Added", "50,000") == "hashes"
        assert IWFReportsScraper._infer_unit("Self-Generated", "45%") == "percent"

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )
        respx.get(url__regex=r".*iwf\.org\.uk.*").respond(
            200, text=SAMPLE_IWF_HTML
        )
        respx.get(url__regex=r".*\.pdf").respond(
            200, content=b"%PDF-1.0 fake content"
        )
        scraper = IWFReportsScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
