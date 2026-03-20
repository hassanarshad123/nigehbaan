"""Tests for the State of Children scraper."""

import pytest
import respx

from data.scrapers.government.stateofchildren import StateOfChildrenScraper


class TestStateOfChildrenScraper:
    def test_init(self):
        scraper = StateOfChildrenScraper()
        assert scraper.name == "stateofchildren"
        assert scraper.priority == "P1"

    def test_parse_tables(self, sample_gov_table_html):
        scraper = StateOfChildrenScraper()
        records = scraper.parse_tables(sample_gov_table_html)
        assert len(records) == 4  # 4 province rows
        assert records[0]["Province"] == "Punjab"

    def test_normalize_record(self):
        scraper = StateOfChildrenScraper()
        raw = {"Province": "KP", "Cases": "234", "Year": "2023"}
        normalized = scraper.normalize_record(raw)
        assert normalized["province"] == "Khyber Pakhtunkhwa"
        assert normalized["cases"] == 234
        assert normalized["source"] == "stateofchildren"

    def test_validate(self):
        scraper = StateOfChildrenScraper()
        assert scraper.validate({"province": "Punjab", "cases": 100, "source": "test"})
        assert not scraper.validate({})

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, sample_gov_table_html):
        respx.get("https://stateofchildren.com/children-dataset/").respond(
            200, text=sample_gov_table_html,
        )
        scraper = StateOfChildrenScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert len(results) > 0
        await scraper.close()
