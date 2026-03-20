"""Tests for the Labour Force Survey scraper."""

import pytest
import respx

from data.scrapers.government.labour_surveys import LabourSurveysScraper


MOCK_CATALOG_HTML = """<html><body>
<h1>Labour Force Survey Reports</h1>
<ul>
  <li><a href="/sites/default/files/lfs_2023_24.pdf">Labour Force Survey 2023-24</a></li>
  <li><a href="/sites/default/files/lfs_2022_23.pdf">Labour Force Survey 2022-23</a></li>
</ul>
</body></html>"""


class TestLabourSurveysScraper:
    def test_init(self):
        scraper = LabourSurveysScraper()
        assert scraper.name == "labour_surveys"
        assert scraper.source_url
        assert scraper.schedule
        assert scraper.priority

    def test_validate_valid(self):
        scraper = LabourSurveysScraper()
        record = {
            "source_name": "labour_surveys",
            "indicator": "lfs_child_labor_rate",
            "report_year": 2024,
            "value": 100.0,
        }
        assert scraper.validate(record) is True

    def test_validate_empty(self):
        scraper = LabourSurveysScraper()
        assert scraper.validate({}) is False

    def test_validate_missing_value(self):
        scraper = LabourSurveysScraper()
        record = {"source_name": "labour_surveys", "indicator": "test"}
        assert scraper.validate(record) is False

    def test_detect_province(self):
        assert LabourSurveysScraper._detect_province("Punjab") == "Punjab"
        assert LabourSurveysScraper._detect_province("kp") == "Khyber Pakhtunkhwa"
        assert LabourSurveysScraper._detect_province("unknown") is None

    def test_detect_gender(self):
        assert LabourSurveysScraper._detect_gender("Female") == "female"
        assert LabourSurveysScraper._detect_gender("Male") == "male"
        assert LabourSurveysScraper._detect_gender("Total") == "total"
        assert LabourSurveysScraper._detect_gender("unknown") is None

    def test_detect_age_bracket(self):
        assert LabourSurveysScraper._detect_age_bracket("5-14 years") == "5-14"
        assert LabourSurveysScraper._detect_age_bracket("no bracket") is None

    def test_extract_year(self):
        assert LabourSurveysScraper._extract_year("lfs_2023_24.pdf") == "2023"
        assert LabourSurveysScraper._extract_year("report_2021.pdf") == "2021"

    def test_parse_numeric(self):
        assert LabourSurveysScraper._parse_numeric("1,234") == 1234.0
        assert LabourSurveysScraper._parse_numeric("-") is None
        assert LabourSurveysScraper._parse_numeric("") is None

    def test_infer_unit(self):
        assert LabourSurveysScraper._infer_unit(45.6) == "percent"
        assert LabourSurveysScraper._infer_unit(12345) == "count"

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, sample_pdf_bytes, raw_data_dir, monkeypatch):
        monkeypatch.setattr(
            "data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir
        )

        catalog_url = "https://www.pbs.gov.pk/content/labour-force-survey"
        respx.get(catalog_url).respond(200, text=MOCK_CATALOG_HTML)
        respx.get(url__regex=r".*\.pdf$").respond(
            200,
            content=sample_pdf_bytes,
            headers={"Content-Type": "application/pdf"},
        )

        scraper = LabourSurveysScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert isinstance(results, list)
        await scraper.close()
