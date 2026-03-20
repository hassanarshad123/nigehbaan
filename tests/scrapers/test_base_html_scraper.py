"""Tests for BaseHTMLTableScraper."""

import pytest

from data.scrapers.base_html_scraper import BaseHTMLTableScraper


class MockHTMLScraper(BaseHTMLTableScraper):
    """Concrete implementation for testing."""

    name = "mock_html"
    source_url = "https://example.com/stats"
    schedule = "0 0 1 */3 *"
    priority = "P2"

    async def scrape(self):
        response = await self.fetch(self.source_url)
        tables = self.extract_tables(response.text)
        records = []
        for table in tables:
            for row in table:
                records.append({
                    "source_name": self.name,
                    "indicator": row.get("Category", ""),
                    "value": row.get("2023", ""),
                })
        return records

    def validate(self, record):
        return bool(record.get("source_name") and record.get("indicator"))


class TestBaseHTMLTableScraper:
    def test_extract_tables(self, sample_gov_table_html):
        scraper = MockHTMLScraper()
        tables = scraper.extract_tables(sample_gov_table_html)
        assert len(tables) == 1
        assert len(tables[0]) == 4  # 4 data rows
        assert tables[0][0]["Province"] == "Punjab"

    def test_extract_tables_empty_html(self):
        scraper = MockHTMLScraper()
        tables = scraper.extract_tables("<html><body></body></html>")
        assert tables == []

    def test_extract_tables_single_row(self):
        scraper = MockHTMLScraper()
        html = "<table><tr><th>A</th></tr></table>"
        tables = scraper.extract_tables(html)
        assert tables == []  # Only header, no data rows

    def test_extract_links(self):
        scraper = MockHTMLScraper()
        html = '''<html><body>
            <a href="/files/report_2024.pdf">Report</a>
            <a href="/page.html">Page</a>
            <a href="/files/data.pdf">Data</a>
        </body></html>'''
        links = scraper.extract_links(html, r"\.pdf$")
        assert len(links) == 2
        assert links[0]["url"] == "/files/report_2024.pdf"

    def test_extract_links_no_matches(self):
        scraper = MockHTMLScraper()
        html = '<a href="/page.html">Page</a>'
        links = scraper.extract_links(html, r"\.xlsx$")
        assert links == []

    def test_normalize_province_known(self):
        assert BaseHTMLTableScraper.normalize_province("punjab") == "Punjab"
        assert BaseHTMLTableScraper.normalize_province("KP") == "Khyber Pakhtunkhwa"
        assert BaseHTMLTableScraper.normalize_province("kpk") == "Khyber Pakhtunkhwa"
        assert BaseHTMLTableScraper.normalize_province("Sindh") == "Sindh"
        assert BaseHTMLTableScraper.normalize_province("baluchistan") == "Balochistan"
        assert BaseHTMLTableScraper.normalize_province("ICT") == "Islamabad Capital Territory"
        assert BaseHTMLTableScraper.normalize_province("AJK") == "Azad Jammu & Kashmir"
        assert BaseHTMLTableScraper.normalize_province("GB") == "Gilgit-Baltistan"

    def test_normalize_province_unknown(self):
        assert BaseHTMLTableScraper.normalize_province("Mars") == "Mars"

    def test_normalize_province_empty(self):
        assert BaseHTMLTableScraper.normalize_province("") == ""

    @pytest.mark.asyncio
    async def test_scrape(self, mock_http, sample_gov_table_html, raw_data_dir, monkeypatch):
        monkeypatch.setattr("data.scrapers.base_scraper.RAW_DATA_DIR", raw_data_dir)
        mock_http.get("https://example.com/stats").respond(200, text=sample_gov_table_html)

        scraper = MockHTMLScraper()
        scraper.rate_limit_delay = 0
        results = await scraper.run()
        assert len(results) == 4
        assert results[0]["source_name"] == "mock_html"
        await scraper.close()
