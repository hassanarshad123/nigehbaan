"""Tests for the World Bank API scraper."""

import pytest
import respx

from data.scrapers.international.worldbank_api import WorldBankAPIScraper, INDICATORS


class TestWorldBankAPIScraper:
    def test_init(self):
        scraper = WorldBankAPIScraper()
        assert scraper.name == "worldbank_api"
        assert scraper.priority == "P2"

    def test_build_api_url(self):
        scraper = WorldBankAPIScraper()
        url = scraper.build_api_url("NY.GDP.PCAP.CD")
        assert "PAK" in url
        assert "NY.GDP.PCAP.CD" in url
        assert "json" in url

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_indicator(self, sample_worldbank_json):
        respx.get(url__regex=r".*worldbank.*").respond(200, json=sample_worldbank_json)
        scraper = WorldBankAPIScraper()
        scraper.rate_limit_delay = 0
        records = await scraper.fetch_indicator("NY.GDP.PCAP.CD")
        assert len(records) == 3
        assert records[0]["indicator_code"] == "NY.GDP.PCAP.CD"
        assert records[0]["year"] == 2023
        assert records[0]["value"] == 1505.0
        await scraper.close()

    def test_validate(self):
        scraper = WorldBankAPIScraper()
        assert scraper.validate({"indicator_code": "X", "year": 2023, "value": 1.0})
        assert not scraper.validate({"indicator_code": "X", "year": 2023})
        assert not scraper.validate({"indicator_code": "X"})

    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape(self, sample_worldbank_json):
        respx.get(url__regex=r".*worldbank.*").respond(200, json=sample_worldbank_json)
        scraper = WorldBankAPIScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.scrape()
        assert len(results) > 0
        assert all(r.get("scraped_at") for r in results)
        await scraper.close()
