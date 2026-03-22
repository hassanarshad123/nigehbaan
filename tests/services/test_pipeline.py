"""Tests for the ArticleProcessingPipeline service.

These tests exercise the ProcessingResult dataclass and pipeline
initialization.  No database or OpenAI API access is involved.
"""

from unittest.mock import patch

import pytest

from app.services.pipeline import ArticleProcessingPipeline, ProcessingResult


# ---------- fixtures ----------


@pytest.fixture
def pipeline():
    """Return a fresh ArticleProcessingPipeline instance."""
    return ArticleProcessingPipeline()


# ---------- ProcessingResult dataclass ----------


def test_processing_result_creation():
    """ProcessingResult should store all provided fields."""
    result = ProcessingResult(
        article_id=42,
        stage="extracted",
        is_relevant=True,
        incident_type="kidnapping",
        incident_id=99,
        confidence=0.87,
        error=None,
    )
    assert result.article_id == 42
    assert result.stage == "extracted"
    assert result.is_relevant is True
    assert result.incident_type == "kidnapping"
    assert result.incident_id == 99
    assert result.confidence == 0.87
    assert result.error is None


def test_processing_result_defaults():
    """ProcessingResult should use correct defaults for optional fields."""
    result = ProcessingResult(article_id=1, stage="filtered", is_relevant=False)
    assert result.incident_type is None
    assert result.incident_id is None
    assert result.confidence == 0.0
    assert result.error is None


def test_processing_result_is_frozen():
    """ProcessingResult should be immutable (frozen dataclass)."""
    result = ProcessingResult(article_id=1, stage="filtered", is_relevant=False)
    with pytest.raises(AttributeError):
        result.article_id = 999


def test_processing_result_error_stage():
    """ProcessingResult should correctly represent an error state."""
    result = ProcessingResult(
        article_id=10,
        stage="error",
        is_relevant=False,
        error="Article not found",
    )
    assert result.stage == "error"
    assert result.error == "Article not found"
    assert result.is_relevant is False


def test_processing_result_all_stages():
    """ProcessingResult should accept all valid stage values."""
    stages = ["filtered", "extracted", "geocoded", "incident_created", "error"]
    for stage in stages:
        result = ProcessingResult(article_id=1, stage=stage, is_relevant=False)
        assert result.stage == stage


def test_processing_result_equality():
    """Two ProcessingResults with the same fields should be equal."""
    a = ProcessingResult(article_id=5, stage="extracted", is_relevant=True, confidence=0.9)
    b = ProcessingResult(article_id=5, stage="extracted", is_relevant=True, confidence=0.9)
    assert a == b


def test_processing_result_inequality():
    """Two ProcessingResults with different fields should not be equal."""
    a = ProcessingResult(article_id=5, stage="extracted", is_relevant=True)
    b = ProcessingResult(article_id=6, stage="extracted", is_relevant=True)
    assert a != b


# ---------- ArticleProcessingPipeline init ----------


def test_pipeline_init(pipeline):
    """Pipeline should initialize with extractor set to None."""
    assert pipeline._extractor is None


def test_pipeline_get_extractor_creates_instance(pipeline):
    """_get_extractor should create an AIExtractor on first call."""
    with patch("app.services.pipeline.settings") as mock_settings:
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.openai_model = "gpt-4o-mini"
        mock_settings.openai_max_concurrent = 5

        extractor = pipeline._get_extractor()

        assert extractor is not None
        assert extractor._api_key == "sk-test-key"
        assert extractor._model == "gpt-4o-mini"


def test_pipeline_get_extractor_returns_same_instance(pipeline):
    """_get_extractor should return the same instance on subsequent calls (lazy init)."""
    with patch("app.services.pipeline.settings") as mock_settings:
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.openai_model = "gpt-4o-mini"
        mock_settings.openai_max_concurrent = 5

        first = pipeline._get_extractor()
        second = pipeline._get_extractor()
        assert first is second


def test_pipeline_get_extractor_uses_settings(pipeline):
    """_get_extractor should read config from settings."""
    with patch("app.services.pipeline.settings") as mock_settings:
        mock_settings.openai_api_key = "sk-custom"
        mock_settings.openai_model = "gpt-4o"
        mock_settings.openai_max_concurrent = 10

        extractor = pipeline._get_extractor()
        assert extractor._api_key == "sk-custom"
        assert extractor._model == "gpt-4o"
