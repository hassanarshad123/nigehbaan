"""District name normalisation and fuzzy matching utilities."""

from __future__ import annotations

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# Common alternate spellings found in Pakistani datasets
_MANUAL_MAPPINGS: dict[str, str] = {
    "d.g. khan": "dera ghazi khan",
    "dg khan": "dera ghazi khan",
    "d.i. khan": "dera ismail khan",
    "di khan": "dera ismail khan",
    "r.y. khan": "rahim yar khan",
    "ry khan": "rahim yar khan",
    "t.t. singh": "toba tek singh",
    "muzaffargarh": "muzaffargarh",
    "muzzafargarh": "muzaffargarh",
    "nawab shah": "shaheed benazirabad",
    "nawabshah": "shaheed benazirabad",
    "jacobabad": "jacobabad",
    "jaccobabad": "jacobabad",
    "peshawar": "peshawar",
    "peshawer": "peshawar",
    "nowshera": "nowshera",
    "noshera": "nowshera",
    "mardan": "mardan",
    "mardaan": "mardan",
}


def strip_diacritics(text: str) -> str:
    """Remove diacritical marks (accents, combining characters) from text."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalise_district_name(name: str) -> str:
    """Normalise a district name for consistent matching.

    Steps:
    1. Lowercase
    2. Strip diacritics
    3. Remove punctuation except spaces
    4. Collapse whitespace
    5. Apply manual alias mappings
    """
    cleaned = strip_diacritics(name.lower().strip())
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return _MANUAL_MAPPINGS.get(cleaned, cleaned)


def fuzzy_match_district(
    query: str,
    candidates: dict[str, str],
    threshold: float = 0.75,
) -> str | None:
    """Match *query* against a dict of ``{normalised_name: pcode}`` using similarity.

    Uses a simple bigram-based Dice coefficient for speed (no external
    dependency on ``fuzzywuzzy`` / ``rapidfuzz``).

    Args:
        query: The district name to look up.
        candidates: Mapping of normalised district names to P-codes.
        threshold: Minimum similarity score (0-1) to accept a match.

    Returns:
        The P-code of the best match, or ``None`` if no match exceeds the threshold.
    """
    norm_query = normalise_district_name(query)

    # Exact match first
    if norm_query in candidates:
        return candidates[norm_query]

    query_bigrams = _bigrams(norm_query)
    if not query_bigrams:
        return None

    best_score = 0.0
    best_pcode: str | None = None

    for name, pcode in candidates.items():
        name_bigrams = _bigrams(name)
        if not name_bigrams:
            continue

        intersection = query_bigrams & name_bigrams
        score = 2.0 * len(intersection) / (len(query_bigrams) + len(name_bigrams))

        if score > best_score:
            best_score = score
            best_pcode = pcode

    if best_score >= threshold:
        logger.debug(
            "Fuzzy matched '%s' -> pcode=%s (score=%.3f)",
            query,
            best_pcode,
            best_score,
        )
        return best_pcode

    return None


def _bigrams(text: str) -> set[str]:
    """Return the set of character bigrams in *text*."""
    if len(text) < 2:
        return set()
    return {text[i: i + 2] for i in range(len(text) - 1)}
