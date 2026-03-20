"""Shared test fixtures for the Nigehbaan test suite."""

from pathlib import Path

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


# ---------- PDF / CSV / Urdu fixtures ----------


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Minimal valid PDF bytes for testing PDF scrapers.

    This is a valid single-page PDF with the text 'Child Labor Statistics'.
    """
    # Minimal valid PDF 1.0 with one page and text
    return (
        b"%PDF-1.0\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        b"BT /F1 12 Tf 100 700 Td (Child Labor Statistics) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"0000000360 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\n"
        b"startxref\n431\n%%EOF"
    )


@pytest.fixture
def sample_csv_content() -> str:
    """Sample CSV content for testing API scrapers."""
    return (
        "ref_area,indicator,sex,age,time,value\n"
        "PAK,SDG_0871_SEX_AGE_RT,SEX_T,AGE_Y5-17,2019,11.5\n"
        "PAK,SDG_0871_SEX_AGE_RT,SEX_M,AGE_Y5-17,2019,14.2\n"
        "PAK,SDG_0871_SEX_AGE_RT,SEX_F,AGE_Y5-17,2019,8.3\n"
        "IND,SDG_0871_SEX_AGE_RT,SEX_T,AGE_Y5-17,2019,10.1\n"
    )


@pytest.fixture
def sample_sdmx_xml() -> str:
    """Sample SDMX XML response for testing ILOSTAT-style API scrapers."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
  <message:DataSet>
    <Series>
      <SeriesKey>
        <Value id="REF_AREA" value="PAK"/>
        <Value id="INDICATOR" value="SDG_0871_SEX_AGE_RT"/>
        <Value id="SEX" value="SEX_T"/>
      </SeriesKey>
      <Obs>
        <ObsDimension value="2019"/>
        <ObsValue value="11.5"/>
      </Obs>
    </Series>
  </message:DataSet>
</message:GenericData>"""


@pytest.fixture
def sample_urdu_html() -> str:
    """Sample Urdu news HTML for testing Urdu scrapers."""
    return """<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head><meta charset="UTF-8"><title>لاہور میں بچوں سے زیادتی کا واقعہ</title></head>
<body>
  <article>
    <h1 class="story-title">لاہور میں بچوں سے زیادتی کا واقعہ</h1>
    <span class="date">20 مارچ 2026</span>
    <div class="story-content">
      <p>لاہور: پولیس نے بچوں سے زیادتی کے الزام میں پانچ ملزمان کو گرفتار کر لیا۔</p>
      <p>ایف آئی اے کی ٹیم نے متعدد مقامات پر چھاپے مارے۔ ملزمان بچوں کی سمگلنگ میں ملوث تھے۔</p>
    </div>
  </article>
</body>
</html>"""


@pytest.fixture
def sample_transparency_html() -> str:
    """Sample transparency report HTML table."""
    return """<html><body>
<table>
  <thead>
    <tr><th>Country</th><th>Period</th><th>CSAM Reports</th><th>Content Removed</th></tr>
  </thead>
  <tbody>
    <tr><td>Pakistan</td><td>H1 2025</td><td>1250000</td><td>98500</td></tr>
    <tr><td>Pakistan</td><td>H2 2024</td><td>1180000</td><td>95200</td></tr>
    <tr><td>India</td><td>H1 2025</td><td>3500000</td><td>245000</td></tr>
  </tbody>
</table>
</body></html>"""


@pytest.fixture
def sample_statistical_record() -> dict:
    """Sample statistical report record for testing save functions."""
    return {
        "source_name": "test_source",
        "report_year": 2024,
        "report_title": "Test Annual Report",
        "indicator": "child_labor_rate",
        "value": 11.5,
        "unit": "percent",
        "geographic_scope": "Pakistan",
        "extraction_method": "pdfplumber",
        "extraction_confidence": 0.95,
    }


@pytest.fixture
def sample_transparency_record() -> dict:
    """Sample transparency report record for testing save functions."""
    return {
        "platform": "Meta",
        "report_period": "H1 2025",
        "country": "Pakistan",
        "metric": "csam_reports",
        "value": 1250000.0,
        "unit": "count",
        "source_url": "https://transparency.meta.com",
    }
