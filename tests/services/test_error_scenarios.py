"""Error scenario and edge case tests for backend services.

Validates graceful handling of invalid inputs, missing configuration,
and boundary conditions in the geocoder, risk scorer, AI extractor,
and NLP pipeline services.
"""

import json

import pytest
import respx

from app.services.ai_extractor import AIExtractor
from app.services.geocoder import PakistanGeocoder
from app.services.nlp_pipeline import TraffickingNLPPipeline
from app.services.risk_scorer import RiskScorer


# ─── Fixtures ─────────────────────────────────────────────────


SAMPLE_GAZETTEER = {
    "lahore": {"lat": 31.5497, "lon": 74.3436, "pcode": "PK0403"},
    "karachi": {"lat": 24.8607, "lon": 67.0011, "pcode": "PK0202"},
}


@pytest.fixture
def geocoder(tmp_path):
    """Return a PakistanGeocoder loaded with a small test gazetteer."""
    path = tmp_path / "gazetteer.json"
    path.write_text(json.dumps(SAMPLE_GAZETTEER), encoding="utf-8")
    return PakistanGeocoder(gazetteer_path=str(path))


@pytest.fixture
def scorer():
    """Return a fresh RiskScorer instance."""
    return RiskScorer()


@pytest.fixture
def nlp():
    """Return a fresh TraffickingNLPPipeline instance."""
    return TraffickingNLPPipeline()


# ═══════════════════════════════════════════════════════════════
# PakistanGeocoder — error scenarios
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_geocoder_unknown_location(geocoder):
    """geocode() for an unknown location should return None when Nominatim is blocked."""
    with respx.mock(assert_all_called=False) as router:
        # Block all external HTTP to prevent Nominatim fallback
        router.route().respond(status_code=500)

        result = await geocoder.geocode("atlantis_fictional_city")
        assert result is None


@pytest.mark.asyncio
async def test_geocoder_empty_string(geocoder):
    """geocode('') should return None — empty string matches no gazetteer entry."""
    with respx.mock(assert_all_called=False) as router:
        router.route().respond(status_code=500)

        result = await geocoder.geocode("")
        assert result is None


def test_geocoder_match_district_empty_string(geocoder):
    """match_district('') hits the substring fallback ('' in any_name is True).

    This is a known quirk of Python substring matching — the empty string is
    a substring of every string, so the fuzzy fallback returns the first
    gazetteer entry it finds.  We assert it returns *some* pcode rather than
    None, documenting the current behavior.
    """
    result = geocoder.match_district("")
    # Empty string matches the first gazetteer entry via `"" in name`
    assert result is not None


def test_geocoder_reverse_geocode_far_away(geocoder):
    """reverse_geocode_district for coordinates far from Pakistan should return None."""
    # Coordinates in Antarctica — well beyond 100km threshold
    result = geocoder.reverse_geocode_district(lat=-80.0, lon=0.0)
    assert result is None


# ═══════════════════════════════════════════════════════════════
# RiskScorer — error scenarios
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_risk_scorer_all_missing_indicators(scorer):
    """calculate_score with an empty dict should return 0.0."""
    score = await scorer.calculate_score("PK_EMPTY", {})
    assert score == 0.0


@pytest.mark.asyncio
async def test_risk_scorer_negative_values(scorer):
    """Negative indicator values should be clamped to 0.0 (pre-normalised)."""
    indicators = {
        "incident_rate_per_100k": -0.5,
        "poverty_headcount_ratio": -1.0,
        "out_of_school_rate": -10.0,
    }
    score = await scorer.calculate_score("PK_NEG", indicators)
    # All negative values are clamped to 0.0 by max(0.0, min(1.0, raw_float))
    assert score == 0.0


@pytest.mark.asyncio
async def test_risk_scorer_values_above_one_clamped(scorer):
    """Indicator values above 1.0 (pre-normalised) should be clamped to 1.0."""
    indicators = {
        "incident_rate_per_100k": 5.0,  # clamped to 1.0
        "poverty_headcount_ratio": 100.0,  # clamped to 1.0
    }
    score = await scorer.calculate_score("PK_HIGH", indicators)
    # Both clamped to 1.0: 1.0*0.25 + 1.0*0.15 = 0.40 * 100 = 40.0
    assert score == 40.0


@pytest.mark.asyncio
async def test_risk_scorer_mixed_none_and_valid(scorer):
    """Mix of None and valid values should only score the valid ones."""
    indicators = {
        "incident_rate_per_100k": None,
        "poverty_headcount_ratio": None,
        "out_of_school_rate": 0.5,
        "brick_kiln_density": None,
    }
    score = await scorer.calculate_score("PK_MIX", indicators)
    # Only out_of_school_rate contributes: 0.5 * 0.15 * 100 = 7.5
    assert score == 7.5


# ═══════════════════════════════════════════════════════════════
# AIExtractor — error scenarios
# ═══════════════════════════════════════════════════════════════


def test_ai_extractor_no_api_key():
    """AIExtractor._ensure_client() should raise ValueError when api_key is empty."""
    extractor = AIExtractor(api_key="")
    with pytest.raises(ValueError, match="AI API key not configured"):
        extractor._ensure_client()


def test_ai_extractor_none_api_key():
    """AIExtractor._ensure_client() should raise ValueError when api_key is None."""
    extractor = AIExtractor(api_key=None)
    with pytest.raises(ValueError, match="AI API key not configured"):
        extractor._ensure_client()


def test_ai_extractor_is_relevant_irrelevant_text():
    """is_relevant() should return False for text with no trafficking keywords."""
    extractor = AIExtractor(api_key="test-key")
    result = extractor.is_relevant(
        "Weather forecast for Islamabad",
        "Clear skies expected throughout the weekend with temperatures around 25C.",
    )
    assert result is False


def test_ai_extractor_is_relevant_relevant_text():
    """is_relevant() should return True for text containing trafficking keywords."""
    extractor = AIExtractor(api_key="test-key")
    result = extractor.is_relevant(
        "Child trafficking ring busted",
        "Police arrested five suspects in connection with child trafficking in Lahore.",
    )
    assert result is True


# ═══════════════════════════════════════════════════════════════
# TraffickingNLPPipeline — error scenarios
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_nlp_pipeline_empty_text(nlp):
    """classify_relevance('') should return (False, 0.0)."""
    is_relevant, confidence = await nlp.classify_relevance("")
    assert is_relevant is False
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_nlp_pipeline_none_input(nlp):
    """classify_relevance(None) should return (False, 0.0) — handled by falsy check."""
    is_relevant, confidence = await nlp.classify_relevance(None)  # type: ignore[arg-type]
    assert is_relevant is False
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_nlp_pipeline_non_english_irrelevant(nlp):
    """Urdu text without trafficking keywords should be classified as not relevant."""
    # Generic Urdu text about weather — no trafficking keywords
    urdu_text = (
        "آج اسلام آباد میں موسم صاف رہے گا۔ "
        "درجہ حرارت پچیس ڈگری تک جائے گا۔ "
        "شہریوں کو چھتری لانے کی ضرورت نہیں۔"
    )
    is_relevant, confidence = await nlp.classify_relevance(urdu_text)
    assert is_relevant is False


@pytest.mark.asyncio
async def test_nlp_pipeline_extract_entities_empty(nlp):
    """extract_entities('') should return dict with empty lists."""
    entities = await nlp.extract_entities("")
    assert isinstance(entities, dict)
    assert entities["locations"] == []
    assert entities["dates"] == []
    assert entities["victims"] == []
    assert entities["perpetrators"] == []


@pytest.mark.asyncio
async def test_nlp_pipeline_extract_entities_none(nlp):
    """extract_entities(None) should return dict with empty lists."""
    entities = await nlp.extract_entities(None)  # type: ignore[arg-type]
    assert isinstance(entities, dict)
    for key in ("locations", "dates", "victims", "perpetrators"):
        assert entities[key] == []
