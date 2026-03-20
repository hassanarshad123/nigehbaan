"""NLP pipeline for trafficking-related text analysis."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Keywords that indicate child protection-related content (English + Urdu transliterations)
_TRAFFICKING_KEYWORDS: list[str] = [
    # Trafficking & exploitation
    "trafficking", "trafficked", "smuggling", "exploitation",
    "modern slavery", "debt bondage",
    # Forced/bonded labor
    "bonded", "forced labor", "forced labour",
    "child labor", "child labour", "brick kiln", "bhatta",
    # Sexual abuse
    "sexual abuse", "rape", "molestation", "sodomy", "incest", "CSA",
    # Kidnapping & missing
    "kidnap", "abduct", "missing child", "missing girl", "missing boy",
    "disappeared",
    # Online exploitation
    "child pornograph", "CSAM", "grooming", "sextortion", "PECA",
    "online exploit",
    # Child marriage
    "child marriage", "early marriage", "underage marriage",
    # Physical abuse & murder
    "physical abuse", "torture", "violence against child",
    "child murder", "infanticide", "honor killing", "honour killing",
    # Begging & organ
    "begging ring", "organ trafficking", "camel jockey",
    # Institutional
    "FIA", "child protection", "Zainab Alert",
    # General
    "child abuse", "abandonment", "abandoned child",
    "medical negligence",
]

_KEYWORD_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in _TRAFFICKING_KEYWORDS),
    re.IGNORECASE,
)


class TraffickingNLPPipeline:
    """NLP pipeline for extracting trafficking-related entities from text."""

    def __init__(self) -> None:
        self.nlp: Any = None  # Lazy-loaded spaCy model

    def _ensure_model(self) -> None:
        """Load the spaCy model on first use."""
        if self.nlp is not None:
            return
        try:
            import spacy

            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model en_core_web_sm")
        except (ImportError, OSError) as exc:
            logger.warning("spaCy model not available: %s — using keyword fallback only", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def classify_relevance(self, text: str) -> tuple[bool, float]:
        """Return ``(is_relevant, confidence_score)`` for the given text.

        Uses keyword density as a heuristic.  When the spaCy model is
        available, named-entity overlap with known trafficking patterns
        increases confidence.
        """
        if not text:
            return False, 0.0

        matches = _KEYWORD_PATTERN.findall(text)
        keyword_density = len(matches) / max(len(text.split()), 1)

        # Simple threshold: at least one keyword hit + density > 0.5%
        is_relevant = len(matches) >= 1 and keyword_density > 0.005
        confidence = min(keyword_density * 100, 1.0) if is_relevant else keyword_density * 50

        return is_relevant, round(confidence, 3)

    async def extract_entities(self, text: str) -> dict[str, list[str]]:
        """Extract geographic, temporal, victim, and perpetrator entities.

        Returns a dict with keys: locations, dates, victims, perpetrators.
        """
        result: dict[str, list[str]] = {
            "locations": [],
            "dates": [],
            "victims": [],
            "perpetrators": [],
        }

        if not text:
            return result

        self._ensure_model()

        if self.nlp is None:
            # Fallback: no spaCy model, return empty
            return result

        doc = self.nlp(text)

        for ent in doc.ents:
            label = ent.label_
            if label in ("GPE", "LOC", "FAC"):
                result["locations"].append(ent.text)
            elif label in ("DATE", "TIME"):
                result["dates"].append(ent.text)
            elif label == "PERSON":
                # Heuristic: if near a perpetrator keyword, classify accordingly
                context = text[max(0, ent.start_char - 60): ent.end_char + 60].lower()
                if any(w in context for w in ("accused", "suspect", "perpetrator", "arrested")):
                    result["perpetrators"].append(ent.text)
                else:
                    result["victims"].append(ent.text)

        # Deduplicate while preserving order
        for key in result:
            result[key] = list(dict.fromkeys(result[key]))

        return result
