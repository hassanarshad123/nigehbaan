"""Contract tests for ALL scrapers in the Nigehbaan pipeline.

Parameterized over every scraper registered in run_scraper.py.
Validates that each scraper:
  - Has required class attributes (name, source_url, schedule, priority)
  - validate() returns a bool
  - rate_limit_delay > 0
"""

import importlib

import pytest

# All scrapers from run_scraper.py (module_path, class_name)
ALL_SCRAPERS = [
    # Original scrapers
    ("data.scrapers.international.worldbank_api", "WorldBankAPIScraper"),
    ("data.scrapers.international.tip_report", "TIPReportScraper"),
    ("data.scrapers.international.unhcr_api", "UNHCRAPIScraper"),
    ("data.scrapers.international.unodc", "UNODCScraper"),
    ("data.scrapers.international.dol_child_labor", "DOLChildLaborScraper"),
    ("data.scrapers.news.dawn_scraper", "DawnScraper"),
    ("data.scrapers.news.tribune_scraper", "TribuneScraper"),
    ("data.scrapers.news.the_news_scraper", "TheNewsScraper"),
    ("data.scrapers.news.ary_scraper", "ARYScraper"),
    ("data.scrapers.news.geo_scraper", "GeoScraper"),
    ("data.scrapers.news.rss_monitor", "RSSMonitor"),
    ("data.scrapers.government.stateofchildren", "StateOfChildrenScraper"),
    ("data.scrapers.government.punjab_police", "PunjabPoliceScraper"),
    ("data.scrapers.government.sindh_police", "SindhPoliceScraper"),
    ("data.scrapers.government.kpcpwc", "KPCPWCScraper"),
    ("data.scrapers.government.ssdo_checker", "SSDOChecker"),
    ("data.scrapers.government.mohr_checker", "MoHRChecker"),
    ("data.scrapers.courts.scp", "SCPScraper"),
    ("data.scrapers.courts.lhc", "LHCScraper"),
    ("data.scrapers.courts.shc", "SHCScraper"),
    ("data.scrapers.courts.phc", "PHCScraper"),
    ("data.scrapers.courts.bhc", "BHCScraper"),
    ("data.scrapers.courts.ihc", "IHCScraper"),
    ("data.scrapers.courts.commonlii", "CommonLIIScraper"),
    # Phase 1: CSA
    ("data.scrapers.government.sahil", "SahilScraper"),
    ("data.scrapers.international.ecpat", "ECPATScraper"),
    ("data.scrapers.government.pahchaan", "PahchaanScraper"),
    ("data.scrapers.international.unicef_pakistan", "UNICEFPakistanScraper"),
    ("data.scrapers.government.ncrc", "NCRCScraper"),
    ("data.scrapers.government.cpwb_punjab", "CPWBPunjabScraper"),
    # Phase 2: Online Exploitation
    ("data.scrapers.international.ncmec", "NCMECScraper"),
    ("data.scrapers.international.iwf_reports", "IWFReportsScraper"),
    ("data.scrapers.international.meta_transparency", "MetaTransparencyScraper"),
    ("data.scrapers.international.google_transparency", "GoogleTransparencyScraper"),
    ("data.scrapers.government.drf_newsletters", "DRFNewslettersScraper"),
    ("data.scrapers.international.weprotect_gta", "WeProtectGTAScraper"),
    ("data.scrapers.government.bytes_for_all", "BytesForAllScraper"),
    # Phase 3: Child Labor
    ("data.scrapers.international.ilostat_api", "ILOSTATAPIScraper"),
    ("data.scrapers.international.dol_annual_report", "DOLAnnualReportScraper"),
    ("data.scrapers.international.dol_tvpra", "DOLTVPRAScraper"),
    ("data.scrapers.government.labour_surveys", "LabourSurveysScraper"),
    ("data.scrapers.international.zenodo_kilns_scraper", "ZenodoKilnsScraper"),
    ("data.scrapers.government.bllf", "BLLFScraper"),
    ("data.scrapers.government.brick_kiln_dashboard", "BrickKilnDashboardScraper"),
    # Phase 4: Cross-border
    ("data.scrapers.international.ctdc_dataset", "CTDCDatasetScraper"),
    ("data.scrapers.international.brookings_bride", "BrookingsBrideScraper"),
    # Phase 5: Urdu news
    ("data.scrapers.news.jang_urdu", "JangUrduScraper"),
    ("data.scrapers.news.express_urdu", "ExpressUrduScraper"),
    ("data.scrapers.news.bbc_urdu", "BBCUrduScraper"),
    ("data.scrapers.news.geo_urdu", "GeoUrduScraper"),
]


def _load_scraper_class(module_path: str, class_name: str):
    """Import and return a scraper class."""
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


@pytest.mark.parametrize(
    "module_path,class_name",
    ALL_SCRAPERS,
    ids=[f"{m.split('.')[-1]}.{c}" for m, c in ALL_SCRAPERS],
)
class TestScraperContract:
    """Contract tests that every scraper must satisfy."""

    def test_has_required_attributes(self, module_path: str, class_name: str):
        cls = _load_scraper_class(module_path, class_name)
        scraper = cls()
        assert hasattr(scraper, "name") and scraper.name, f"{class_name} missing name"
        assert hasattr(scraper, "source_url") and scraper.source_url, f"{class_name} missing source_url"
        assert hasattr(scraper, "schedule"), f"{class_name} missing schedule"
        assert hasattr(scraper, "priority"), f"{class_name} missing priority"

    def test_rate_limit_delay_positive(self, module_path: str, class_name: str):
        cls = _load_scraper_class(module_path, class_name)
        scraper = cls()
        assert scraper.rate_limit_delay > 0, f"{class_name} rate_limit_delay must be > 0"

    def test_validate_returns_bool(self, module_path: str, class_name: str):
        cls = _load_scraper_class(module_path, class_name)
        scraper = cls()
        # Empty record should return False
        result = scraper.validate({})
        assert isinstance(result, bool), f"{class_name}.validate() must return bool"
        assert result is False, f"{class_name}.validate({{}}) should return False"

    def test_validate_accepts_valid_record(self, module_path: str, class_name: str):
        cls = _load_scraper_class(module_path, class_name)
        scraper = cls()
        # Build a minimal valid record based on scraper type
        record = _build_sample_record(scraper)
        result = scraper.validate(record)
        assert isinstance(result, bool), f"{class_name}.validate() must return bool"


def _build_sample_record(scraper) -> dict:
    """Build a sample record appropriate for the scraper type."""
    name = scraper.name

    # News scrapers expect url, title, published_date, full_text
    news_names = {
        "dawn", "tribune", "the_news", "ary_news", "geo_news",
        "rss_monitor", "jang_urdu", "express_urdu", "bbc_urdu", "geo_urdu",
    }
    if name in news_names:
        return {
            "url": "https://example.com/article",
            "title": "Test Article",
            "published_date": "2026-01-01",
            "full_text": "Test article body text about child trafficking.",
        }

    # Statistical report scrapers
    return {
        "source_name": name,
        "indicator": "test_indicator",
        "report_title": "Test Report",
        "report_year": 2024,
        "value": 100.0,
    }
