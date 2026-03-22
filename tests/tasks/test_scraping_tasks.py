"""Tests for scraping_tasks Celery task registration, COURT_SCRAPERS dict,
and helper functions."""

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixture: stub celery_app so scraping_tasks can import without a broker
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_celery(monkeypatch):
    """Stub celery_app.task to a pass-through decorator."""
    fake_celery = MagicMock()

    def _task_decorator(**kwargs):
        def wrapper(fn):
            fn.name = kwargs.get("name", fn.__name__)
            fn.max_retries = kwargs.get("max_retries")
            fn.autoretry_for = kwargs.get("autoretry_for")
            fn.retry_backoff = kwargs.get("retry_backoff")
            fn.bind = kwargs.get("bind", False)
            fn.delay = MagicMock()
            fn.apply_async = MagicMock()
            return fn
        return wrapper

    fake_celery.task = _task_decorator
    monkeypatch.setitem(
        __import__("sys").modules,
        "app.tasks.celery_app",
        MagicMock(celery_app=fake_celery),
    )


def _import_scraping_tasks():
    import importlib
    import sys
    mod_name = "app.tasks.scraping_tasks"
    # Also clear processing_tasks since scraping_tasks references it
    for name in list(sys.modules):
        if name.startswith("app.tasks."):
            del sys.modules[name]
    return importlib.import_module(mod_name)


# ---------------------------------------------------------------------------
# COURT_SCRAPERS dict completeness
# ---------------------------------------------------------------------------

class TestCourtScrapersDict:
    """Validate the COURT_SCRAPERS mapping used by scrape_courts."""

    def test_court_scrapers_has_seven_entries(self):
        mod = _import_scraping_tasks()
        assert len(mod.COURT_SCRAPERS) == 7

    def test_court_scrapers_keys(self):
        mod = _import_scraping_tasks()
        expected_keys = {"scp", "lhc", "shc", "phc", "bhc", "ihc", "commonlii"}
        assert set(mod.COURT_SCRAPERS.keys()) == expected_keys

    def test_court_scrapers_values_are_tuples(self):
        mod = _import_scraping_tasks()
        for key, value in mod.COURT_SCRAPERS.items():
            assert isinstance(value, tuple), f"{key} value is not a tuple"
            assert len(value) == 2, f"{key} tuple does not have 2 elements"

    def test_court_scrapers_module_paths_start_with_data(self):
        mod = _import_scraping_tasks()
        for key, (module_path, _class_name) in mod.COURT_SCRAPERS.items():
            assert module_path.startswith("data.scrapers.courts."), (
                f"{key} module path does not start with data.scrapers.courts."
            )

    def test_court_scrapers_class_names_end_with_scraper(self):
        mod = _import_scraping_tasks()
        for key, (_module_path, class_name) in mod.COURT_SCRAPERS.items():
            assert class_name.endswith("Scraper"), (
                f"{key} class name '{class_name}' does not end with 'Scraper'"
            )

    def test_commonlii_entry_present(self):
        mod = _import_scraping_tasks()
        assert "commonlii" in mod.COURT_SCRAPERS
        module_path, class_name = mod.COURT_SCRAPERS["commonlii"]
        assert "commonlii" in module_path
        assert class_name == "CommonLIIScraper"


# ---------------------------------------------------------------------------
# Task registration tests
# ---------------------------------------------------------------------------

class TestScrapingTaskRegistration:
    """Verify key scraping tasks are registered with proper names."""

    def test_scrape_news_rss_registered(self):
        mod = _import_scraping_tasks()
        assert hasattr(mod, "scrape_news_rss")
        assert mod.scrape_news_rss.name == "app.tasks.scraping_tasks.scrape_news_rss"

    def test_scrape_courts_registered(self):
        mod = _import_scraping_tasks()
        assert hasattr(mod, "scrape_courts")
        assert mod.scrape_courts.name == "app.tasks.scraping_tasks.scrape_courts"

    def test_scrape_tip_report_registered(self):
        mod = _import_scraping_tasks()
        assert hasattr(mod, "scrape_tip_report")
        assert mod.scrape_tip_report.name == "app.tasks.scraping_tasks.scrape_tip_report"

    def test_scrape_worldbank_api_registered(self):
        mod = _import_scraping_tasks()
        assert hasattr(mod, "scrape_worldbank_api")
        assert mod.scrape_worldbank_api.name == "app.tasks.scraping_tasks.scrape_worldbank_api"

    def test_update_ctdc_registered(self):
        mod = _import_scraping_tasks()
        assert hasattr(mod, "update_ctdc")
        assert mod.update_ctdc.name == "app.tasks.scraping_tasks.update_ctdc"


# ---------------------------------------------------------------------------
# _make_stat_task helper
# ---------------------------------------------------------------------------

class TestMakeStatTask:
    """Verify the _make_stat_task helper exists and is callable."""

    def test_make_stat_task_exists(self):
        mod = _import_scraping_tasks()
        assert hasattr(mod, "_make_stat_task")
        assert callable(mod._make_stat_task)

    def test_make_transparency_task_exists(self):
        mod = _import_scraping_tasks()
        assert hasattr(mod, "_make_transparency_task")
        assert callable(mod._make_transparency_task)

    def test_make_news_task_exists(self):
        mod = _import_scraping_tasks()
        assert hasattr(mod, "_make_news_task")
        assert callable(mod._make_news_task)


# ---------------------------------------------------------------------------
# POLICE_SCRAPERS dict
# ---------------------------------------------------------------------------

class TestPoliceScrapersDict:
    """Validate the POLICE_SCRAPERS mapping."""

    def test_police_scrapers_has_expected_provinces(self):
        mod = _import_scraping_tasks()
        assert "punjab" in mod.POLICE_SCRAPERS
        assert "sindh" in mod.POLICE_SCRAPERS

    def test_police_scrapers_values_are_tuples(self):
        mod = _import_scraping_tasks()
        for key, value in mod.POLICE_SCRAPERS.items():
            assert isinstance(value, tuple)
            assert len(value) == 2
