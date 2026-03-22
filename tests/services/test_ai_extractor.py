"""Tests for the AIExtractor service.

These tests exercise pure-logic helpers, data classes, and keyword
pre-filtering.  No OpenAI API calls or database access is involved.
"""

import pytest

from app.services.ai_extractor import (
    INCIDENT_TYPES,
    VALID_INCIDENT_TYPES,
    VALID_SUB_TYPES,
    AIExtractor,
    ExtractionResult,
    LocationExtraction,
    _safe_float,
    _safe_int,
)


# ---------- fixtures ----------


@pytest.fixture
def extractor():
    """Return an AIExtractor with a dummy API key (no real calls)."""
    return AIExtractor(api_key="sk-test-dummy-key")


# ---------- INCIDENT_TYPES taxonomy ----------


def test_incident_types_is_dict():
    """INCIDENT_TYPES should be a non-empty dict."""
    assert isinstance(INCIDENT_TYPES, dict)
    assert len(INCIDENT_TYPES) > 0


def test_incident_types_keys_are_strings():
    """Every key in INCIDENT_TYPES should be a string."""
    for key in INCIDENT_TYPES:
        assert isinstance(key, str), f"Key {key!r} is not a string"


def test_incident_types_values_are_lists():
    """Every value in INCIDENT_TYPES should be a list of strings."""
    for key, subs in INCIDENT_TYPES.items():
        assert isinstance(subs, list), f"Value for '{key}' is not a list"
        for sub in subs:
            assert isinstance(sub, str), f"Sub-type {sub!r} under '{key}' is not a string"


def test_incident_types_contains_expected_keys():
    """INCIDENT_TYPES must include core incident categories."""
    expected = {"kidnapping", "child_trafficking", "sexual_abuse", "child_labor", "child_marriage"}
    assert expected.issubset(INCIDENT_TYPES.keys())


# ---------- VALID_INCIDENT_TYPES frozenset ----------


def test_valid_incident_types_is_frozenset():
    """VALID_INCIDENT_TYPES should be a frozenset."""
    assert isinstance(VALID_INCIDENT_TYPES, frozenset)


def test_valid_incident_types_matches_keys():
    """VALID_INCIDENT_TYPES must exactly match INCIDENT_TYPES keys."""
    assert VALID_INCIDENT_TYPES == frozenset(INCIDENT_TYPES.keys())


def test_valid_sub_types_contains_known_values():
    """VALID_SUB_TYPES should contain known sub-types."""
    assert "rape" in VALID_SUB_TYPES
    assert "brick_kiln" in VALID_SUB_TYPES
    assert "csam" in VALID_SUB_TYPES


# ---------- _safe_float ----------


def test_safe_float_with_valid_float():
    """A valid float string should be converted."""
    assert _safe_float("3.14") == 3.14


def test_safe_float_with_int():
    """An integer should be converted to float."""
    assert _safe_float(42) == 42.0


def test_safe_float_with_none():
    """None should return the default."""
    assert _safe_float(None) == 0.0


def test_safe_float_with_none_custom_default():
    """None should return the custom default when provided."""
    assert _safe_float(None, 5.5) == 5.5


def test_safe_float_with_invalid_string():
    """An invalid string should return the default."""
    assert _safe_float("not-a-number") == 0.0


def test_safe_float_with_empty_string():
    """An empty string should return the default."""
    assert _safe_float("") == 0.0


# ---------- _safe_int ----------


def test_safe_int_with_valid_int():
    """A valid integer should be converted."""
    assert _safe_int(7) == 7


def test_safe_int_with_float():
    """A float should be truncated to int."""
    assert _safe_int(3.9) == 3


def test_safe_int_with_string_int():
    """A string integer should be converted."""
    assert _safe_int("12") == 12


def test_safe_int_with_none():
    """None should return None."""
    assert _safe_int(None) is None


def test_safe_int_with_invalid_string():
    """An invalid string should return None."""
    assert _safe_int("abc") is None


# ---------- LocationExtraction dataclass ----------


def test_location_extraction_creation():
    """LocationExtraction should store provided values."""
    loc = LocationExtraction(name="Lahore", district="Lahore", province="Punjab", confidence=0.95)
    assert loc.name == "Lahore"
    assert loc.district == "Lahore"
    assert loc.province == "Punjab"
    assert loc.confidence == 0.95


def test_location_extraction_defaults():
    """LocationExtraction should use correct defaults for optional fields."""
    loc = LocationExtraction(name="Karachi")
    assert loc.district is None
    assert loc.province is None
    assert loc.confidence == 0.0


def test_location_extraction_is_frozen():
    """LocationExtraction should be immutable (frozen dataclass)."""
    loc = LocationExtraction(name="Quetta")
    with pytest.raises(AttributeError):
        loc.name = "Modified"


# ---------- ExtractionResult dataclass ----------


def test_extraction_result_creation():
    """ExtractionResult should store all provided fields."""
    result = ExtractionResult(
        is_relevant=True,
        confidence=0.92,
        incident_type="kidnapping",
        sub_type=None,
        victim_count=2,
        victim_age_min=8,
        victim_age_max=12,
        victim_gender="female",
    )
    assert result.is_relevant is True
    assert result.confidence == 0.92
    assert result.incident_type == "kidnapping"
    assert result.victim_count == 2


def test_extraction_result_defaults():
    """ExtractionResult should use correct defaults for optional fields."""
    result = ExtractionResult(is_relevant=False, confidence=0.0)
    assert result.incident_type is None
    assert result.sub_type is None
    assert result.victim_count is None
    assert result.ppc_sections == []
    assert result.locations == []
    assert result.raw_extraction == {}
    assert result.english_translation is None


def test_extraction_result_is_frozen():
    """ExtractionResult should be immutable (frozen dataclass)."""
    result = ExtractionResult(is_relevant=True, confidence=0.5)
    with pytest.raises(AttributeError):
        result.is_relevant = False


# ---------- AIExtractor init ----------


def test_extractor_init_stores_params():
    """AIExtractor should store init parameters."""
    ext = AIExtractor(api_key="sk-test", model="gpt-4o", max_concurrent=3, base_url="https://custom.api")
    assert ext._api_key == "sk-test"
    assert ext._model == "gpt-4o"
    assert ext._base_url == "https://custom.api"


def test_extractor_init_defaults():
    """AIExtractor should use correct defaults."""
    ext = AIExtractor()
    assert ext._api_key is None
    assert ext._model == "gpt-4o-mini"
    assert ext._base_url is None
    assert ext._client is None


def test_extractor_ensure_client_raises_without_key():
    """_ensure_client should raise ValueError when no API key is set."""
    ext = AIExtractor(api_key=None)
    with pytest.raises(ValueError, match="AI API key not configured"):
        ext._ensure_client()


# ---------- keyword pre-filter ----------


def test_is_relevant_with_trafficking_keyword(extractor):
    """Articles containing trafficking keywords should pass the pre-filter."""
    assert extractor.is_relevant("Child trafficking ring busted", "Police arrested suspects")


def test_is_relevant_with_urdu_keyword(extractor):
    """Articles containing Urdu keywords should pass the pre-filter."""
    assert extractor.is_relevant("", "بچوں سے زیادتی کے الزام")


def test_is_relevant_returns_false_for_unrelated(extractor):
    """Articles without relevant keywords should not pass the pre-filter."""
    assert extractor.is_relevant("Weather update", "Clear skies expected tomorrow") is False


def test_is_relevant_case_insensitive(extractor):
    """Keyword matching should be case-insensitive."""
    assert extractor.is_relevant("CHILD TRAFFICKING REPORT", "Details of the case")


# ---------- _parse_extraction ----------


def test_parse_extraction_full_data():
    """_parse_extraction should correctly parse a complete response."""
    data = {
        "is_relevant": True,
        "confidence": 0.85,
        "incident_type": "kidnapping",
        "sub_type": None,
        "victim_count": 3,
        "victim_age_min": 6,
        "victim_age_max": 10,
        "victim_gender": "female",
        "perpetrator_type": "stranger",
        "ppc_sections": ["370", "371"],
        "incident_date": "2026-03-15",
        "locations": [
            {"name": "Lahore", "district": "Lahore", "province": "Punjab"}
        ],
    }
    result = AIExtractor._parse_extraction(data)
    assert result.is_relevant is True
    assert result.confidence == 0.85
    assert result.incident_type == "kidnapping"
    assert result.victim_count == 3
    assert len(result.locations) == 1
    assert result.locations[0].name == "Lahore"


def test_parse_extraction_invalid_incident_type_becomes_other():
    """Unknown incident_type should be remapped to 'other'."""
    data = {"is_relevant": True, "confidence": 0.5, "incident_type": "unknown_type_xyz"}
    result = AIExtractor._parse_extraction(data)
    assert result.incident_type == "other"


def test_parse_extraction_invalid_sub_type_becomes_none():
    """Unknown sub_type should be set to None."""
    data = {"is_relevant": True, "confidence": 0.5, "sub_type": "invalid_sub_xyz"}
    result = AIExtractor._parse_extraction(data)
    assert result.sub_type is None


def test_parse_extraction_empty_data():
    """_parse_extraction should handle an empty dict gracefully."""
    result = AIExtractor._parse_extraction({})
    assert result.is_relevant is False
    assert result.confidence == 0.0
    assert result.incident_type is None
    assert result.locations == []
