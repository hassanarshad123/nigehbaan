"""Tests for the RiskScorer service.

These tests exercise the pure scoring logic — no database or async I/O
is involved beyond the async method signature.
"""

import pytest

from app.services.risk_scorer import RiskScorer


# ---------- fixtures ----------


@pytest.fixture
def scorer():
    """Return a fresh RiskScorer instance."""
    return RiskScorer()


def _zero_indicators() -> dict[str, float]:
    """Return all indicators set to 0."""
    return {name: 0.0 for name in RiskScorer.WEIGHTS}


def _max_indicators() -> dict[str, float]:
    """Return all indicators set to 1.0 (pre-normalised max)."""
    return {name: 1.0 for name in RiskScorer.WEIGHTS}


def _mixed_indicators() -> dict[str, float]:
    """Return a representative mix of indicator values."""
    return {
        "incident_rate_per_100k": 0.8,
        "poverty_headcount_ratio": 0.6,
        "out_of_school_rate": 0.7,
        "brick_kiln_density": 0.5,
        "child_labor_rate": 0.4,
        "border_proximity": 0.3,
        "flood_affected_pct": 0.2,
        "conviction_rate_inverse": 0.9,
        "child_marriage_rate": 0.1,
        "refugee_population_ratio": 0.6,
    }


# ---------- weights validation ----------


def test_weights_sum_to_one():
    """All configured weights must sum to exactly 1.0."""
    total = sum(RiskScorer.WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"


def test_all_weights_are_positive():
    """Every weight must be strictly positive."""
    for name, weight in RiskScorer.WEIGHTS.items():
        assert weight > 0, f"Weight for '{name}' is {weight}, expected > 0"


def test_weights_have_ten_indicators():
    """The scorer should define exactly 10 indicators."""
    assert len(RiskScorer.WEIGHTS) == 10


# ---------- calculate_score — boundary values ----------


@pytest.mark.asyncio
async def test_score_all_zeros(scorer):
    """All indicators at 0 should produce a score of 0."""
    score = await scorer.calculate_score("PK_TEST", _zero_indicators())
    assert score == 0.0


@pytest.mark.asyncio
async def test_score_all_max(scorer):
    """All indicators at 1.0 (pre-normalised) should produce a score of 100."""
    score = await scorer.calculate_score("PK_TEST", _max_indicators())
    assert score == 100.0


# ---------- calculate_score — mixed values ----------


@pytest.mark.asyncio
async def test_score_mixed_values(scorer):
    """Mixed indicator values should produce a score between 0 and 100."""
    score = await scorer.calculate_score("PK_TEST", _mixed_indicators())
    assert 0.0 < score < 100.0


@pytest.mark.asyncio
async def test_score_mixed_deterministic(scorer):
    """Same inputs must always produce the same score."""
    indicators = _mixed_indicators()
    score_a = await scorer.calculate_score("PK_TEST", indicators)
    score_b = await scorer.calculate_score("PK_TEST", indicators)
    assert score_a == score_b


@pytest.mark.asyncio
async def test_score_mixed_correct_value(scorer):
    """Verify the exact expected score for the mixed indicator set."""
    indicators = _mixed_indicators()
    # Manual calculation:
    # 0.8*0.25 + 0.6*0.15 + 0.7*0.15 + 0.5*0.10 + 0.4*0.10
    # + 0.3*0.05 + 0.2*0.05 + 0.9*0.05 + 0.1*0.05 + 0.6*0.05
    # = 0.20 + 0.09 + 0.105 + 0.05 + 0.04 + 0.015 + 0.01 + 0.045 + 0.005 + 0.03
    # = 0.59
    # * 100 = 59.0
    score = await scorer.calculate_score("PK_TEST", indicators)
    assert score == 59.0


# ---------- missing indicator handling ----------


@pytest.mark.asyncio
async def test_score_empty_indicators(scorer):
    """An empty indicators dict should produce a score of 0."""
    score = await scorer.calculate_score("PK_TEST", {})
    assert score == 0.0


@pytest.mark.asyncio
async def test_score_partial_indicators(scorer):
    """Providing only some indicators should only use those weights."""
    partial = {
        "incident_rate_per_100k": 1.0,
        "poverty_headcount_ratio": 1.0,
    }
    score = await scorer.calculate_score("PK_TEST", partial)
    # 1.0*0.25 + 1.0*0.15 = 0.40 * 100 = 40.0
    assert score == 40.0


@pytest.mark.asyncio
async def test_score_ignores_unknown_indicators(scorer):
    """Indicators not in WEIGHTS should be silently ignored."""
    indicators = {
        "incident_rate_per_100k": 0.5,
        "unknown_indicator": 999.0,
    }
    score = await scorer.calculate_score("PK_TEST", indicators)
    # Only incident_rate_per_100k is recognised: 0.5 * 0.25 * 100 = 12.5
    assert score == 12.5


@pytest.mark.asyncio
async def test_score_handles_none_value(scorer):
    """An indicator value of None should be skipped."""
    indicators = {
        "incident_rate_per_100k": None,
        "poverty_headcount_ratio": 1.0,
    }
    score = await scorer.calculate_score("PK_TEST", indicators)
    # Only poverty_headcount_ratio: 1.0 * 0.15 * 100 = 15.0
    assert score == 15.0


@pytest.mark.asyncio
async def test_score_handles_non_numeric_value(scorer):
    """Non-numeric indicator values should be skipped."""
    indicators = {
        "incident_rate_per_100k": "not-a-number",
        "poverty_headcount_ratio": 1.0,
    }
    score = await scorer.calculate_score("PK_TEST", indicators)
    assert score == 15.0


# ---------- range_lookup normalisation ----------


@pytest.mark.asyncio
async def test_score_with_range_lookup(scorer):
    """When range_lookup is provided, raw values are min-max normalised."""
    indicators = {
        "incident_rate_per_100k": 50.0,
        "poverty_headcount_ratio": 30.0,
    }
    range_lookup = {
        "incident_rate_per_100k": (0.0, 100.0),    # normalised: 0.5
        "poverty_headcount_ratio": (10.0, 50.0),    # normalised: 0.5
    }
    score = await scorer.calculate_score(
        "PK_TEST", indicators, range_lookup=range_lookup
    )
    # 0.5*0.25 + 0.5*0.15 = 0.125 + 0.075 = 0.20 * 100 = 20.0
    assert score == 20.0


@pytest.mark.asyncio
async def test_normalise_equal_min_max():
    """If min == max, _normalise should return 0.0 (avoids division by zero)."""
    result = RiskScorer._normalise(5.0, 5.0, 5.0)
    assert result == 0.0


@pytest.mark.asyncio
async def test_normalise_clamps_above_max():
    """Values above max should be clamped to 1.0."""
    result = RiskScorer._normalise(150.0, 0.0, 100.0)
    assert result == 1.0


@pytest.mark.asyncio
async def test_normalise_clamps_below_min():
    """Values below min should be clamped to 0.0."""
    result = RiskScorer._normalise(-10.0, 0.0, 100.0)
    assert result == 0.0
