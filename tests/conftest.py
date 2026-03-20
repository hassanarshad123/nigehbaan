"""Shared test fixtures for the Nigehbaan test suite."""

import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

import pytest
import httpx
import respx


# ---------- Paths ----------

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def raw_data_dir(tmp_path: Path) -> Path:
    """Temporary raw data directory for scraper output."""
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    return raw


# ---------- HTTP mocking ----------


@pytest.fixture
def mock_http():
    """respx router for mocking httpx requests.

    Usage:
        def test_something(mock_http):
            mock_http.get("https://example.com/api").respond(200, json={...})
            # scraper.fetch("https://example.com/api") now returns mocked response
    """
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
def make_response():
    """Factory for creating httpx.Response objects for testing."""

    def _make(
        status_code: int = 200,
        text: str = "",
        json_data: dict | list | None = None,
        content: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        if json_data is not None:
            return httpx.Response(
                status_code,
                json=json_data,
                headers=headers or {},
            )
        if content:
            return httpx.Response(
                status_code,
                content=content,
                headers=headers or {},
            )
        return httpx.Response(
            status_code,
            text=text,
            headers=headers or {},
        )

    return _make


# ---------- Sample data factories ----------


@pytest.fixture
def sample_rss_xml() -> str:
    """Sample RSS feed XML for testing RSS parsers."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test News Feed</title>
    <link>https://example.com</link>
    <item>
      <title>Child trafficking ring busted in Lahore</title>
      <link>https://example.com/article/1</link>
      <pubDate>Thu, 20 Mar 2026 10:00:00 +0500</pubDate>
      <description>Police arrested five suspects in connection with child trafficking.</description>
    </item>
    <item>
      <title>Weather update for Karachi</title>
      <link>https://example.com/article/2</link>
      <pubDate>Thu, 20 Mar 2026 11:00:00 +0500</pubDate>
      <description>Clear skies expected for the weekend.</description>
    </item>
    <item>
      <title>Missing children found in Faisalabad raid</title>
      <link>https://example.com/article/3</link>
      <pubDate>Thu, 20 Mar 2026 12:00:00 +0500</pubDate>
      <description>Three missing children recovered during police operation.</description>
    </item>
  </channel>
</rss>"""


@pytest.fixture
def sample_article_html() -> str:
    """Sample news article HTML for testing article scrapers."""
    return """<!DOCTYPE html>
<html>
<head><title>Child trafficking ring busted in Lahore</title></head>
<body>
  <article>
    <h1 class="story__title">Child trafficking ring busted in Lahore</h1>
    <span class="story__byline">By Staff Reporter</span>
    <time datetime="2026-03-20">March 20, 2026</time>
    <div class="story__content">
      <p>LAHORE: Police on Thursday arrested five suspects in connection
      with a child trafficking ring operating in the Lahore district.</p>
      <p>The FIA team conducted raids at multiple locations following
      intelligence reports about the gang that was allegedly involved in
      kidnapping and selling children under sections 366-A and 370 of the
      Pakistan Penal Code.</p>
      <p>Three children, aged between 8 and 12 years, were recovered
      during the operation. The suspects have been booked under relevant
      sections of the PPC and PECA 2016.</p>
    </div>
    <div class="story__tags">
      <a href="/tag/crime">Crime</a>
      <a href="/tag/lahore">Lahore</a>
    </div>
  </article>
</body>
</html>"""


@pytest.fixture
def sample_court_html() -> str:
    """Sample court search result HTML for testing court scrapers."""
    return """<html>
<body>
<table class="table" id="results">
  <thead>
    <tr>
      <th>Sr. No.</th>
      <th>Case Number</th>
      <th>Year</th>
      <th>Parties</th>
      <th>Date Decided</th>
      <th>Result</th>
      <th>PDF</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>Cr.A. 123/2024</td>
      <td>2024</td>
      <td>State vs Muhammad Ali — Section 370, 371-A PPC</td>
      <td>15-01-2024</td>
      <td>Conviction</td>
      <td><a href="/download/judgment_123_2024.pdf">Download</a></td>
    </tr>
    <tr>
      <td>2</td>
      <td>W.P. 456/2024</td>
      <td>2024</td>
      <td>Mst. Fatima vs SHO — Section 366-A PPC</td>
      <td>20-02-2024</td>
      <td>Disposed</td>
      <td><a href="/download/judgment_456_2024.pdf">Download</a></td>
    </tr>
    <tr>
      <td>3</td>
      <td>Cr.A. 789/2024</td>
      <td>2024</td>
      <td>State vs Ahmad — Section 302 PPC</td>
      <td>10-03-2024</td>
      <td>Acquitted</td>
      <td><a href="/download/judgment_789_2024.pdf">Download</a></td>
    </tr>
  </tbody>
</table>
</body>
</html>"""


@pytest.fixture
def sample_gov_table_html() -> str:
    """Sample government statistics HTML table."""
    return """<html>
<body>
<table class="data-table">
  <thead>
    <tr>
      <th>Province</th>
      <th>Category</th>
      <th>2022</th>
      <th>2023</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Punjab</td>
      <td>Child Trafficking</td>
      <td>234</td>
      <td>267</td>
    </tr>
    <tr>
      <td>Sindh</td>
      <td>Child Trafficking</td>
      <td>156</td>
      <td>189</td>
    </tr>
    <tr>
      <td>KP</td>
      <td>Child Trafficking</td>
      <td>89</td>
      <td>102</td>
    </tr>
    <tr>
      <td>Balochistan</td>
      <td>Child Trafficking</td>
      <td>45</td>
      <td>58</td>
    </tr>
  </tbody>
</table>
</body>
</html>"""


@pytest.fixture
def sample_worldbank_json() -> dict:
    """Sample World Bank API response."""
    return [
        {"page": 1, "pages": 1, "per_page": 100, "total": 3},
        [
            {
                "indicator": {"id": "NY.GDP.PCAP.CD", "value": "GDP per capita"},
                "country": {"id": "PK", "value": "Pakistan"},
                "date": "2023",
                "value": 1505.0,
            },
            {
                "indicator": {"id": "NY.GDP.PCAP.CD", "value": "GDP per capita"},
                "country": {"id": "PK", "value": "Pakistan"},
                "date": "2022",
                "value": 1497.0,
            },
            {
                "indicator": {"id": "NY.GDP.PCAP.CD", "value": "GDP per capita"},
                "country": {"id": "PK", "value": "Pakistan"},
                "date": "2021",
                "value": 1538.0,
            },
        ],
    ]


@pytest.fixture
def sample_geojson() -> dict:
    """Sample GeoJSON for testing boundary/kiln downloads."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"ADM2_EN": "Lahore", "ADM2_PCODE": "PK0401"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[74.2, 31.4], [74.5, 31.4], [74.5, 31.7], [74.2, 31.7], [74.2, 31.4]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"ADM2_EN": "Faisalabad", "ADM2_PCODE": "PK0403"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[73.0, 31.2], [73.3, 31.2], [73.3, 31.5], [73.0, 31.5], [73.0, 31.2]]],
                },
            },
        ],
    }
