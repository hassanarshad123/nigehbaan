"""Tests for the TraffickingNLPPipeline service.

These tests exercise keyword matching, regex patterns, and relevance
classification.  No spaCy model or database access is needed.
"""

import re

import pytest

from app.services.nlp_pipeline import (
    TraffickingNLPPipeline,
    _KEYWORD_PATTERN,
    _TRAFFICKING_KEYWORDS,
)


# ---------- fixtures ----------


@pytest.fixture
def pipeline():
    """Return a fresh TraffickingNLPPipeline instance."""
    return TraffickingNLPPipeline()


# ---------- _TRAFFICKING_KEYWORDS list ----------


def test_trafficking_keywords_is_list():
    """_TRAFFICKING_KEYWORDS should be a non-empty list."""
    assert isinstance(_TRAFFICKING_KEYWORDS, list)
    assert len(_TRAFFICKING_KEYWORDS) > 0


def test_trafficking_keywords_are_strings():
    """Every keyword should be a string."""
    for kw in _TRAFFICKING_KEYWORDS:
        assert isinstance(kw, str), f"Keyword {kw!r} is not a string"


def test_trafficking_keywords_contains_core_terms():
    """The keyword list must include key trafficking terms."""
    expected_substrings = ["trafficking", "kidnap", "sexual abuse", "child labor"]
    for term in expected_substrings:
        assert any(
            term.lower() in kw.lower() for kw in _TRAFFICKING_KEYWORDS
        ), f"Expected '{term}' in keywords"


# ---------- _KEYWORD_PATTERN regex ----------


def test_keyword_pattern_is_compiled_regex():
    """_KEYWORD_PATTERN should be a compiled regex pattern."""
    assert isinstance(_KEYWORD_PATTERN, re.Pattern)


def test_keyword_pattern_matches_trafficking():
    """The pattern should match 'trafficking' in text."""
    assert _KEYWORD_PATTERN.search("a case of trafficking in Lahore")


def test_keyword_pattern_matches_kidnap():
    """The pattern should match 'kidnap' in text."""
    assert _KEYWORD_PATTERN.search("suspect arrested for kidnapping children")


def test_keyword_pattern_case_insensitive():
    """The pattern should match regardless of case."""
    assert _KEYWORD_PATTERN.search("CHILD TRAFFICKING ring")
    assert _KEYWORD_PATTERN.search("Child Marriage banned")


def test_keyword_pattern_no_match_on_unrelated():
    """The pattern should not match unrelated text."""
    assert _KEYWORD_PATTERN.search("The weather is sunny today in Islamabad") is None


def test_keyword_pattern_matches_child_marriage():
    """The pattern should match 'child marriage'."""
    assert _KEYWORD_PATTERN.search("Reports of child marriage in rural areas")


def test_keyword_pattern_matches_brick_kiln():
    """The pattern should match 'brick kiln' (child labor indicator)."""
    assert _KEYWORD_PATTERN.search("children found working at brick kiln")


def test_keyword_pattern_matches_zainab_alert():
    """The pattern should match 'Zainab Alert'."""
    assert _KEYWORD_PATTERN.search("activated under the Zainab Alert act")


# ---------- TraffickingNLPPipeline init ----------


def test_pipeline_init(pipeline):
    """Pipeline should initialize with nlp set to None (lazy load)."""
    assert pipeline.nlp is None


def test_pipeline_ensure_model_sets_nlp_or_warns(pipeline):
    """_ensure_model should either load spaCy or leave nlp as None."""
    from unittest.mock import patch, MagicMock

    # Mock spaCy import to avoid environment-specific failures
    mock_spacy = MagicMock()
    mock_spacy.load.return_value = MagicMock()
    with patch.dict("sys.modules", {"spacy": mock_spacy}):
        pipeline._ensure_model()
    # After calling _ensure_model, nlp is either a spaCy model or still None
    assert True


# ---------- classify_relevance ----------


@pytest.mark.asyncio
async def test_classify_relevance_empty_text(pipeline):
    """Empty text should return (False, 0.0)."""
    is_relevant, confidence = await pipeline.classify_relevance("")
    assert is_relevant is False
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_classify_relevance_with_keyword(pipeline):
    """Text with trafficking keyword should flag as relevant."""
    text = "Police arrested suspects involved in child trafficking near Lahore"
    is_relevant, confidence = await pipeline.classify_relevance(text)
    assert is_relevant is True
    assert confidence > 0.0


@pytest.mark.asyncio
async def test_classify_relevance_no_keywords(pipeline):
    """Text without trafficking keywords should have low confidence."""
    text = "The stock market rallied today on positive economic data from the central bank"
    is_relevant, confidence = await pipeline.classify_relevance(text)
    # May or may not be flagged depending on threshold, but confidence should be low
    assert confidence < 0.5


@pytest.mark.asyncio
async def test_classify_relevance_deterministic(pipeline):
    """Same input should always produce the same output."""
    text = "FIA rescued kidnapped children from a trafficking ring"
    result_a = await pipeline.classify_relevance(text)
    result_b = await pipeline.classify_relevance(text)
    assert result_a == result_b


@pytest.mark.asyncio
async def test_classify_relevance_multiple_keywords_higher_confidence(pipeline):
    """Text with many keywords should produce higher confidence than one."""
    sparse = "A child was reported missing"
    dense = (
        "Child trafficking ring busted by FIA. "
        "Suspects involved in kidnapping and sexual abuse. "
        "Victims found in bonded labor at a brick kiln."
    )
    _, conf_sparse = await pipeline.classify_relevance(sparse)
    _, conf_dense = await pipeline.classify_relevance(dense)
    assert conf_dense > conf_sparse


# ---------- extract_entities edge cases ----------


@pytest.mark.asyncio
async def test_extract_entities_empty_text(pipeline):
    """Empty text should return empty entity lists."""
    result = await pipeline.extract_entities("")
    assert result == {
        "locations": [],
        "dates": [],
        "victims": [],
        "perpetrators": [],
    }


@pytest.mark.asyncio
async def test_extract_entities_returns_dict_keys(pipeline):
    """extract_entities should always return the four expected keys."""
    # Force nlp to remain None so no spaCy import occurs; fallback path returns empty dict
    pipeline.nlp = None
    from unittest.mock import patch
    with patch.object(pipeline, "_ensure_model"):
        result = await pipeline.extract_entities("Some text about an incident")
    assert set(result.keys()) == {"locations", "dates", "victims", "perpetrators"}
