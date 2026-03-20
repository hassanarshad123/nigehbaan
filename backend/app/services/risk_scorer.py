"""Composite trafficking vulnerability risk scorer."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RiskScorer:
    """Calculate a composite trafficking vulnerability score (0-100) for districts.

    The score is a weighted sum of normalised indicators.  Each raw indicator
    is normalised to the 0-1 range using min-max scaling across all districts
    before the weights are applied.
    """

    WEIGHTS: dict[str, float] = {
        "incident_rate_per_100k": 0.25,
        "poverty_headcount_ratio": 0.15,
        "out_of_school_rate": 0.15,
        "brick_kiln_density": 0.10,
        "child_labor_rate": 0.10,
        "border_proximity": 0.05,
        "flood_affected_pct": 0.05,
        "conviction_rate_inverse": 0.05,
        "child_marriage_rate": 0.05,
        "refugee_population_ratio": 0.05,
    }

    @staticmethod
    def _normalise(value: float, min_val: float, max_val: float) -> float:
        """Min-max normalise *value* to the 0-1 range."""
        if max_val == min_val:
            return 0.0
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    async def calculate_score(
        self,
        district_pcode: str,
        indicators: dict[str, Any],
        *,
        range_lookup: dict[str, tuple[float, float]] | None = None,
    ) -> float:
        """Calculate the weighted composite score for a single district.

        Parameters
        ----------
        district_pcode:
            The district's P-code (used for logging only).
        indicators:
            A dict mapping indicator names (matching ``WEIGHTS`` keys) to their
            raw values for this district.
        range_lookup:
            Optional dict mapping indicator names to ``(min, max)`` tuples used
            for normalisation.  If ``None``, indicators are assumed to already be
            in the 0-1 range.

        Returns
        -------
        float
            Composite score in the range 0-100.
        """
        score = 0.0

        for indicator_name, weight in self.WEIGHTS.items():
            raw = indicators.get(indicator_name)
            if raw is None:
                continue

            raw_float = float(raw)

            if range_lookup and indicator_name in range_lookup:
                lo, hi = range_lookup[indicator_name]
                normalised = self._normalise(raw_float, lo, hi)
            else:
                normalised = max(0.0, min(1.0, raw_float))

            score += normalised * weight

        final_score = round(score * 100, 2)
        logger.debug("Risk score for %s: %.2f", district_pcode, final_score)
        return final_score
