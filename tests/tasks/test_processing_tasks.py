"""Tests for processing_tasks Celery task registration, configuration, and helpers."""

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Import helpers — these tests verify task metadata without triggering
# the full Celery/DB stack, so we mock celery_app at import time.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_celery(monkeypatch):
    """Stub celery_app.task so processing_tasks can import without a broker."""
    fake_celery = MagicMock()

    # Make the .task() decorator pass the function through, attaching attrs
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


def _import_processing_tasks():
    """Force a fresh import of processing_tasks after monkeypatching."""
    import importlib
    import sys
    mod_name = "app.tasks.processing_tasks"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    return importlib.import_module(mod_name)


# ---------------------------------------------------------------------------
# Task registration tests
# ---------------------------------------------------------------------------

class TestTaskRegistration:
    """Verify that every expected task is registered with the correct name."""

    def test_process_article_ai_registered(self):
        mod = _import_processing_tasks()
        assert hasattr(mod, "process_article_ai")
        assert mod.process_article_ai.name == "app.tasks.processing_tasks.process_article_ai"

    def test_process_pdf_registered(self):
        mod = _import_processing_tasks()
        assert hasattr(mod, "process_pdf")
        assert mod.process_pdf.name == "app.tasks.processing_tasks.process_pdf"

    def test_geocode_incidents_registered(self):
        mod = _import_processing_tasks()
        assert hasattr(mod, "geocode_incidents")
        assert mod.geocode_incidents.name == "app.tasks.processing_tasks.geocode_incidents"

    def test_calculate_risk_scores_registered(self):
        mod = _import_processing_tasks()
        assert hasattr(mod, "calculate_risk_scores")
        assert mod.calculate_risk_scores.name == "app.tasks.processing_tasks.calculate_risk_scores"

    def test_run_nlp_pipeline_registered(self):
        mod = _import_processing_tasks()
        assert hasattr(mod, "run_nlp_pipeline")
        assert mod.run_nlp_pipeline.name == "app.tasks.processing_tasks.run_nlp_pipeline"

    def test_process_court_judgment_registered(self):
        mod = _import_processing_tasks()
        assert hasattr(mod, "process_court_judgment")
        assert mod.process_court_judgment.name == "app.tasks.processing_tasks.process_court_judgment"

    def test_update_vulnerability_indicators_registered(self):
        mod = _import_processing_tasks()
        assert hasattr(mod, "update_vulnerability_indicators")
        assert mod.update_vulnerability_indicators.name == (
            "app.tasks.processing_tasks.update_vulnerability_indicators"
        )

    def test_derive_trafficking_routes_registered(self):
        mod = _import_processing_tasks()
        assert hasattr(mod, "derive_trafficking_routes")
        assert mod.derive_trafficking_routes.name == (
            "app.tasks.processing_tasks.derive_trafficking_routes"
        )


# ---------------------------------------------------------------------------
# Task configuration tests
# ---------------------------------------------------------------------------

class TestTaskConfiguration:
    """Verify retry / backoff settings on each task."""

    def test_process_article_ai_retry_config(self):
        mod = _import_processing_tasks()
        task = mod.process_article_ai
        assert task.max_retries == 3
        assert task.retry_backoff == 30
        assert task.bind is True

    def test_process_pdf_retry_config(self):
        mod = _import_processing_tasks()
        task = mod.process_pdf
        assert task.max_retries == 3
        assert task.retry_backoff == 60

    def test_geocode_incidents_retry_config(self):
        mod = _import_processing_tasks()
        task = mod.geocode_incidents
        assert task.max_retries == 3
        assert task.retry_backoff == 60

    def test_derive_routes_retry_config(self):
        mod = _import_processing_tasks()
        task = mod.derive_trafficking_routes
        assert task.max_retries == 1


# ---------------------------------------------------------------------------
# _classify_court_incident helper tests
# ---------------------------------------------------------------------------

class TestClassifyCourtIncident:
    """Unit tests for the _classify_court_incident pure function."""

    def test_none_sections_defaults_to_trafficking(self):
        mod = _import_processing_tasks()
        assert mod._classify_court_incident(None) == "trafficking"

    def test_empty_list_defaults_to_trafficking(self):
        mod = _import_processing_tasks()
        assert mod._classify_court_incident([]) == "trafficking"

    def test_kidnapping_sections(self):
        mod = _import_processing_tasks()
        assert mod._classify_court_incident(["364-A"]) == "kidnapping"
        assert mod._classify_court_incident(["365"]) == "kidnapping"

    def test_trafficking_sections(self):
        mod = _import_processing_tasks()
        assert mod._classify_court_incident(["370"]) == "trafficking"
        assert mod._classify_court_incident(["371-A"]) == "trafficking"

    def test_sexual_abuse_section(self):
        mod = _import_processing_tasks()
        assert mod._classify_court_incident(["377"]) == "sexual_abuse"

    def test_forced_labor_section(self):
        mod = _import_processing_tasks()
        assert mod._classify_court_incident(["374"]) == "forced_labor"

    def test_unknown_section_defaults_to_trafficking(self):
        mod = _import_processing_tasks()
        assert mod._classify_court_incident(["302"]) == "trafficking"


# ---------------------------------------------------------------------------
# _run_async helper test
# ---------------------------------------------------------------------------

class TestRunAsync:
    """Verify the _run_async helper can execute a trivial coroutine."""

    def test_run_async_returns_result(self):
        mod = _import_processing_tasks()

        async def _coro():
            return 42

        result = mod._run_async(_coro())
        assert result == 42
