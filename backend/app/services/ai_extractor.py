"""AI-powered article extraction using OpenAI GPT-4o-mini.

Provides structured extraction of incident data from news articles,
including Urdu translation and entity extraction. Uses a keyword
pre-filter to minimize API costs (~$0.0003/article).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Incident type taxonomy — the canonical list for the entire platform
# ---------------------------------------------------------------------------

INCIDENT_TYPES: dict[str, list[str]] = {
    "kidnapping": [],
    "child_trafficking": [],
    "sexual_abuse": ["rape", "sodomy", "incest", "molestation"],
    "sexual_exploitation": [],
    "online_exploitation": ["csam", "grooming", "sextortion"],
    "child_labor": [
        "brick_kiln", "domestic_work", "factory", "agriculture",
        "street_vending", "auto_workshop",
    ],
    "bonded_labor": [],
    "child_marriage": [],
    "child_murder": ["infanticide"],
    "honor_killing": [],
    "begging_ring": [],
    "organ_trafficking": [],
    "missing": [],
    "physical_abuse": [],
    "child_pornography": [],
    "abandonment": [],
    "medical_negligence": [],
    "other": [],
}

# All valid incident type values (top-level keys)
VALID_INCIDENT_TYPES: frozenset[str] = frozenset(INCIDENT_TYPES.keys())

# All valid sub-types (flattened)
VALID_SUB_TYPES: frozenset[str] = frozenset(
    sub for subs in INCIDENT_TYPES.values() for sub in subs
)

# ---------------------------------------------------------------------------
# Keyword pre-filter — free, runs before any OpenAI call
# ---------------------------------------------------------------------------

RELEVANCE_KEYWORDS_EN: list[str] = [
    # Trafficking & exploitation
    "child trafficking", "human trafficking", "traffick", "smuggling",
    "forced labor", "forced labour", "bonded lab", "modern slavery",
    "debt bondage", "slavery",
    # Sexual abuse
    "sexual abuse", "rape", "molestation", "sodomy", "incest",
    "child sexual", "CSA",
    # Kidnapping & missing
    "kidnap", "abduct", "missing child", "missing girl", "missing boy",
    "disappeared",
    # Online exploitation
    "child pornograph", "CSAM", "grooming", "sextortion", "PECA",
    "online exploit",
    # Child labor
    "child lab", "child work", "brick kiln", "bhatta", "minor employ",
    # Child marriage
    "child marriage", "early marriage", "underage marriage", "nikah",
    # Physical abuse & murder
    "physical abuse", "beat", "torture", "violence against child",
    "child murder", "infanticide", "honor killing", "honour killing",
    # Begging & organ
    "begging ring", "organ trafficking", "camel jockey",
    # Legal codes
    "366-A", "366-B", "370", "371", "377", "292-A", "292-B", "zina",
    # Institutional
    "FIA", "child protection", "Zainab Alert",
    # General
    "child abuse", "minor", "exploit",
    "abandonment", "abandoned child", "medical negligence",
]

RELEVANCE_KEYWORDS_UR: list[str] = [
    "بچوں سے زیادتی",
    "اغوا",
    "جنسی زیادتی",
    "بچوں کی اسمگلنگ",
    "جبری مشقت",
    "بچوں کی شادی",
    "لاپتہ بچے",
    "بچوں کا قتل",
    "بھٹہ مزدوری",
    "غیرت کے نام پر",
    "زینب الرٹ",
]

_ALL_KEYWORDS: list[str] = RELEVANCE_KEYWORDS_EN + RELEVANCE_KEYWORDS_UR
_KEYWORD_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in _ALL_KEYWORDS),
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LocationExtraction:
    """A single location extracted from article text."""

    name: str
    district: str | None = None
    province: str | None = None
    confidence: float = 0.0


@dataclass(frozen=True)
class ExtractionResult:
    """Structured output from AI extraction of a news article."""

    is_relevant: bool
    confidence: float
    incident_type: str | None = None
    sub_type: str | None = None
    victim_count: int | None = None
    victim_age_min: int | None = None
    victim_age_max: int | None = None
    victim_gender: str | None = None
    perpetrator_type: str | None = None
    ppc_sections: list[str] = field(default_factory=list)
    incident_date: str | None = None
    locations: list[LocationExtraction] = field(default_factory=list)
    raw_extraction: dict[str, Any] = field(default_factory=dict)
    english_translation: str | None = None


# ---------------------------------------------------------------------------
# OpenAI extraction prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a child protection intelligence analyst for Pakistan."
    " Extract structured information from news articles about incidents involving children.\n"
    "\n"
    "You MUST respond with valid JSON matching this schema:\n"
    "{\n"
    '  "is_relevant": boolean,\n'
    '  "confidence": float (0.0-1.0),\n'
    '  "incident_type": string | null,\n'
    '  "sub_type": string | null,\n'
    '  "victim_count": integer | null,\n'
    '  "victim_age_min": integer | null,\n'
    '  "victim_age_max": integer | null,\n'
    '  "victim_gender": "male" | "female" | "mixed" | "unknown" | null,\n'
    '  "perpetrator_type": string | null,\n'
    '  "ppc_sections": [string],\n'
    '  "incident_date": "YYYY-MM-DD" | null,\n'
    '  "locations": [{"name": string, "district": string|null, "province": string|null}]\n'
    "}\n"
    "\n"
    "Valid incident_type values: kidnapping, child_trafficking, sexual_abuse,"
    " sexual_exploitation, online_exploitation, child_labor, bonded_labor,"
    " child_marriage, child_murder, honor_killing, begging_ring, organ_trafficking,"
    " missing, physical_abuse, child_pornography, abandonment, medical_negligence, other\n"
    "\n"
    "Valid sub_type values for child_labor:"
    " brick_kiln, domestic_work, factory, agriculture, street_vending, auto_workshop\n"
    "Valid sub_type values for sexual_abuse: rape, sodomy, incest, molestation\n"
    "Valid sub_type values for online_exploitation: csam, grooming, sextortion\n"
    "Valid sub_type values for child_murder: infanticide\n"
    "\n"
    "perpetrator_type values:"
    " family, neighbor, teacher, employer, stranger, gang, online_predator, institution, unknown\n"
    "\n"
    "Pakistan provinces:"
    " Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan, Islamabad, AJK, Gilgit-Baltistan\n"
    "\n"
    "If the article is NOT about a child protection issue,"
    " set is_relevant=false and leave other fields null."
)

_URDU_SYSTEM_PROMPT = _SYSTEM_PROMPT + (
    "\n\n"
    "The article is in Urdu. First translate to English mentally, then extract."
    " Also provide an english_translation field with a concise English"
    " translation of the article (max 500 words).\n"
    "\n"
    "Add to the JSON schema:\n"
    '  "english_translation": string'
)


# ---------------------------------------------------------------------------
# AIExtractor class
# ---------------------------------------------------------------------------

class AIExtractor:
    """AI-powered extraction service using OpenAI GPT-4o-mini.

    Usage::

        extractor = AIExtractor(api_key="sk-...")
        result = await extractor.extract_structured(title, text, url)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        max_concurrent: int = 5,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._client: Any = None

    def _ensure_client(self) -> Any:
        """Lazy-initialize the OpenAI async client (compatible with OpenRouter)."""
        if self._client is not None:
            return self._client

        if not self._api_key:
            raise ValueError(
                "AI API key not configured. Set OPENAI_API_KEY in .env"
            )

        try:
            from openai import AsyncOpenAI
            kwargs: dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = AsyncOpenAI(**kwargs)
            return self._client
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )

    # ------------------------------------------------------------------
    # Keyword pre-filter (free, no API call)
    # ------------------------------------------------------------------

    def is_relevant(self, title: str, text: str) -> bool:
        """Fast keyword pre-filter. Returns True if article might be relevant.

        This runs before any OpenAI call to save costs. Only articles
        passing this filter are sent to the AI for structured extraction.
        """
        combined = f"{title} {text}"
        return bool(_KEYWORD_PATTERN.search(combined))

    # ------------------------------------------------------------------
    # Structured extraction via OpenAI
    # ------------------------------------------------------------------

    async def extract_structured(
        self,
        title: str,
        text: str,
        source_url: str,
    ) -> ExtractionResult:
        """Extract structured incident data from an English article.

        Args:
            title: Article headline.
            text: Article body text.
            source_url: Original article URL (for logging).

        Returns:
            ExtractionResult with all extracted fields.
        """
        client = self._ensure_client()

        user_content = (
            f"Article URL: {source_url}\n"
            f"Title: {title}\n\n"
            f"Text:\n{text[:6000]}"
        )

        async with self._semaphore:
            try:
                response = await client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=1000,
                )

                raw_text = response.choices[0].message.content or "{}"
                data = json.loads(raw_text)
                return self._parse_extraction(data)

            except Exception as exc:
                logger.error(
                    "OpenAI extraction failed for %s: %s", source_url, exc,
                )
                return ExtractionResult(
                    is_relevant=False,
                    confidence=0.0,
                    raw_extraction={"error": str(exc)},
                )

    async def extract_from_urdu(
        self,
        title: str,
        text: str,
        source_url: str,
    ) -> ExtractionResult:
        """Extract structured data from an Urdu article, including translation.

        Args:
            title: Urdu article headline.
            text: Urdu article body text.
            source_url: Original article URL.

        Returns:
            ExtractionResult with english_translation populated.
        """
        client = self._ensure_client()

        user_content = (
            f"Article URL: {source_url}\n"
            f"Title: {title}\n\n"
            f"Text:\n{text[:6000]}"
        )

        async with self._semaphore:
            try:
                response = await client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": _URDU_SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=1500,
                )

                raw_text = response.choices[0].message.content or "{}"
                data = json.loads(raw_text)
                return self._parse_extraction(data)

            except Exception as exc:
                logger.error(
                    "OpenAI Urdu extraction failed for %s: %s",
                    source_url, exc,
                )
                return ExtractionResult(
                    is_relevant=False,
                    confidence=0.0,
                    raw_extraction={"error": str(exc)},
                )

    async def extract_batch(
        self,
        articles: list[dict[str, Any]],
    ) -> list[ExtractionResult]:
        """Extract structured data from a batch of articles concurrently.

        Each article dict must have keys: title, text, source_url.
        Optional key: language ("ur" for Urdu, default "en").

        Args:
            articles: List of article dicts.

        Returns:
            List of ExtractionResult in the same order.
        """
        tasks = []
        for article in articles:
            title = article.get("title", "")
            text = article.get("text", "") or article.get("full_text", "")
            url = article.get("source_url", "") or article.get("url", "")
            language = article.get("language", "en")

            if language == "ur":
                tasks.append(self.extract_from_urdu(title, text, url))
            else:
                tasks.append(self.extract_structured(title, text, url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        parsed: list[ExtractionResult] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Batch extraction error: %s", result)
                parsed.append(ExtractionResult(
                    is_relevant=False,
                    confidence=0.0,
                    raw_extraction={"error": str(result)},
                ))
            else:
                parsed.append(result)

        return parsed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_extraction(data: dict[str, Any]) -> ExtractionResult:
        """Parse raw OpenAI JSON response into an ExtractionResult."""
        locations = []
        for loc in data.get("locations", []) or []:
            if isinstance(loc, dict):
                locations.append(LocationExtraction(
                    name=loc.get("name", ""),
                    district=loc.get("district"),
                    province=loc.get("province"),
                ))

        incident_type = data.get("incident_type")
        if incident_type and incident_type not in VALID_INCIDENT_TYPES:
            incident_type = "other"

        sub_type = data.get("sub_type")
        if sub_type and sub_type not in VALID_SUB_TYPES:
            sub_type = None

        return ExtractionResult(
            is_relevant=bool(data.get("is_relevant", False)),
            confidence=_safe_float(data.get("confidence"), 0.0),
            incident_type=incident_type,
            sub_type=sub_type,
            victim_count=_safe_int(data.get("victim_count")),
            victim_age_min=_safe_int(data.get("victim_age_min")),
            victim_age_max=_safe_int(data.get("victim_age_max")),
            victim_gender=data.get("victim_gender"),
            perpetrator_type=data.get("perpetrator_type"),
            ppc_sections=data.get("ppc_sections") or [],
            incident_date=data.get("incident_date"),
            locations=locations,
            raw_extraction=data,
            english_translation=data.get("english_translation"),
        )


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float, returning default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value: Any) -> int | None:
    """Convert a value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
