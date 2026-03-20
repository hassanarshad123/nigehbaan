"""News article NER and geocoding parser.

NLP pipeline for extracting structured information from Pakistani
news articles about trafficking and child abuse.

Priority: P1
"""

from pathlib import Path
from typing import Any
import json
import re
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

CRIME_TYPES: list[str] = [
    "kidnapping", "child_trafficking", "sexual_abuse", "sexual_exploitation",
    "online_exploitation", "child_labor", "bonded_labor", "child_marriage",
    "child_murder", "honor_killing", "begging_ring", "organ_trafficking",
    "missing", "physical_abuse", "child_pornography", "abandonment",
    "medical_negligence", "other",
]

# Keyword → crime type mapping
CRIME_KEYWORDS: dict[str, list[str]] = {
    "kidnapping": ["kidnap", "kidnapping", "366-A", "366-B", "369", "abduct", "abduction", "snatch"],
    "child_trafficking": ["child trafficking", "human trafficking", "traffick", "sold", "buying", "selling", "smuggling"],
    "sexual_abuse": ["sexual abuse", "rape", "molestation", "sodomy", "incest", "zina", "377", "CSA"],
    "sexual_exploitation": ["sexual exploit", "prostitut", "commercial sex"],
    "online_exploitation": ["CSAM", "grooming", "sextortion", "online exploit", "online abuse", "cyber"],
    "child_labor": ["child lab", "child work", "minor employ", "factory work", "street vend"],
    "bonded_labor": ["bonded lab", "brick kiln", "bhatta", "forced lab", "slave", "370", "371", "debt bondage"],
    "child_marriage": ["child marriage", "early marriage", "underage marriage", "nikah"],
    "child_murder": ["child murder", "infanticide", "killed child", "murder of minor"],
    "honor_killing": ["honor killing", "honour killing", "karo kari", "ghairat"],
    "begging_ring": ["begging ring", "begging racket", "forced begging"],
    "organ_trafficking": ["organ trafficking", "organ harvest", "organ trade"],
    "missing": ["missing child", "missing girl", "missing boy", "disappeared", "lost child"],
    "physical_abuse": ["physical abuse", "beat", "torture", "violence against child"],
    "child_pornography": ["child pornograph", "292-A", "292-B", "PECA"],
    "abandonment": ["abandon", "abandoned child", "left child", "deserted"],
    "medical_negligence": ["medical negligence", "hospital negligence", "denied treatment"],
}

DEFAULT_GAZETTEER_PATH = Path("data/config/gazetteer/pakistan_districts.json")


class NewsArticleParser:
    """NER and geocoding pipeline for Pakistani news articles."""

    def __init__(
        self, gazetteer_path: Path = DEFAULT_GAZETTEER_PATH
    ) -> None:
        self.nlp_model = None
        self.gazetteer_path = gazetteer_path
        self.gazetteer: dict[str, Any] = {}
        self._variant_lookup: dict[str, dict[str, Any]] = {}

    def load_nlp_model(self) -> None:
        """Load the spaCy NLP model for news article NER."""
        try:
            import spacy
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy en_core_web_sm model")
            except OSError:
                logger.warning("en_core_web_sm not found, NER features limited")
        except ImportError:
            logger.warning("spaCy not installed, NER features disabled")

    def load_gazetteer(self) -> None:
        """Load the Pakistan district gazetteer for geocoding."""
        if not self.gazetteer_path.exists():
            logger.warning("Gazetteer not found: %s", self.gazetteer_path)
            return

        try:
            data = json.loads(self.gazetteer_path.read_text(encoding="utf-8"))
            self.gazetteer = data
            for district in data.get("districts", []):
                pcode = district.get("pcode", "")
                entry = {
                    "pcode": pcode,
                    "name_en": district.get("name_en", ""),
                    "province": district.get("province", ""),
                }
                for variant in district.get("variants", []):
                    self._variant_lookup[variant.lower()] = entry
                self._variant_lookup[district.get("name_en", "").lower()] = entry
            logger.info("Loaded gazetteer with %d variants", len(self._variant_lookup))
        except Exception as exc:
            logger.error("Error loading gazetteer: %s", exc)

    def extract_entities(self, text: str) -> dict[str, list[dict[str, Any]]]:
        """Extract named entities from article text using spaCy."""
        if self.nlp_model is None:
            self.load_nlp_model()

        entities: dict[str, list[dict[str, Any]]] = {
            "GPE": [], "LOC": [], "PERSON": [], "ORG": [], "DATE": [], "CARDINAL": [],
        }

        if self.nlp_model is None:
            return entities

        doc = self.nlp_model(text[:10000])
        seen: set[str] = set()
        for ent in doc.ents:
            key = f"{ent.label_}:{ent.text}"
            if key not in seen and ent.label_ in entities:
                seen.add(key)
                entities[ent.label_].append({
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "label": ent.label_,
                })

        return entities

    def extract_locations(self, text: str) -> list[dict[str, Any]]:
        """Extract geographic locations from article text."""
        locations: list[dict[str, Any]] = []
        seen: set[str] = set()

        # spaCy NER
        entities = self.extract_entities(text)
        for ent in entities.get("GPE", []) + entities.get("LOC", []):
            name = ent["text"]
            if name.lower() not in seen:
                seen.add(name.lower())
                locations.append({
                    "name": name,
                    "type": "ner_extracted",
                    "context": text[max(0, ent["start"] - 50):ent["end"] + 50],
                })

        # Pattern matching for Pakistan locations
        if not self._variant_lookup:
            self.load_gazetteer()
        text_lower = text.lower()
        for variant, info in self._variant_lookup.items():
            if variant in text_lower and variant not in seen:
                seen.add(variant)
                locations.append({
                    "name": info["name_en"],
                    "type": "gazetteer_match",
                    "pcode": info["pcode"],
                    "province": info["province"],
                })

        return locations

    def extract_temporal(self, text: str) -> dict[str, Any]:
        """Extract temporal information from article text."""
        result: dict[str, Any] = {}

        # Date patterns
        date_patterns = [
            (re.compile(r"on\s+(\w+day),?\s+(\w+\s+\d{1,2},?\s+\d{4})", re.IGNORECASE), None),
            (re.compile(r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})", re.IGNORECASE), "%d %B %Y"),
            (re.compile(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})", re.IGNORECASE), "%B %d %Y"),
            (re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})"), None),
        ]

        for pattern, fmt in date_patterns:
            match = pattern.search(text[:3000])
            if match:
                result["incident_date_raw"] = match.group(0)
                break

        return result

    def classify_crime_type(self, text: str) -> tuple[str, float]:
        """Classify the type of crime described in the article."""
        text_lower = text.lower()
        scores: dict[str, int] = {}

        for crime_type, keywords in CRIME_KEYWORDS.items():
            score = sum(
                text_lower.count(kw.lower())
                for kw in keywords
            )
            if score > 0:
                scores[crime_type] = score

        if not scores:
            return ("other", 0.0)

        best_type = max(scores, key=scores.get)
        total_matches = sum(scores.values())
        confidence = min(scores[best_type] / max(total_matches, 1), 1.0)
        return (best_type, round(confidence, 2))

    def extract_victim_info(self, text: str) -> dict[str, Any]:
        """Extract victim demographic information."""
        result: dict[str, Any] = {}

        age_patterns = [
            re.compile(r"aged?\s+(\d{1,2})\s*(?:years?|yrs?)", re.IGNORECASE),
            re.compile(r"(\d{1,2})\s*(?:years?|yrs?)\s*old", re.IGNORECASE),
            re.compile(r"(\d{1,2})\s*-?\s*year\s*-?\s*old", re.IGNORECASE),
        ]
        for pattern in age_patterns:
            match = pattern.search(text)
            if match:
                age = int(match.group(1))
                if 0 < age <= 18:
                    result["victim_age"] = age
                    break

        # Gender
        text_lower = text.lower()
        female = sum(text_lower.count(w) for w in ["girl", "daughter", "woman", "she ", "her "])
        male = sum(text_lower.count(w) for w in ["boy", "son", " he ", " his "])
        if female > male:
            result["victim_gender"] = "female"
        elif male > female:
            result["victim_gender"] = "male"

        # Count
        count_match = re.search(r"(\d+)\s+(?:children|victims|minors|girls|boys)", text, re.IGNORECASE)
        if count_match:
            result["victim_count"] = int(count_match.group(1))

        # Minor indicator
        if "minor" in text_lower:
            result["is_minor"] = True

        return result

    def extract_perpetrator_info(self, text: str) -> dict[str, Any]:
        """Extract perpetrator information from article text."""
        result: dict[str, Any] = {}

        arrest_patterns = [
            re.compile(r"arrested\s+(\d+)\s+(?:suspect|accused|person)", re.IGNORECASE),
            re.compile(r"(?:suspect|accused)\s+(.+?)\s+(?:was|were|has been)\s+arrested", re.IGNORECASE),
        ]
        for pattern in arrest_patterns:
            match = pattern.search(text)
            if match:
                result["arrest_info"] = match.group(0)[:200]
                break

        text_lower = text.lower()
        if "arrested" in text_lower:
            result["arrest_status"] = "arrested"
        elif "absconding" in text_lower or "at large" in text_lower:
            result["arrest_status"] = "at_large"

        # Relationship to victim
        relationships = {
            "family": ["father", "mother", "uncle", "aunt", "step-father", "relative"],
            "neighbor": ["neighbor", "neighbour"],
            "teacher": ["teacher", "tutor", "madrassa"],
            "employer": ["employer", "owner", "malik"],
            "stranger": ["stranger", "unknown"],
        }
        for rel_type, keywords in relationships.items():
            if any(kw in text_lower for kw in keywords):
                result["relationship_to_victim"] = rel_type
                break

        return result

    def geocode_location(
        self, location_name: str
    ) -> dict[str, Any] | None:
        """Geocode a location name using the Pakistan gazetteer."""
        if not self._variant_lookup:
            self.load_gazetteer()

        name_lower = location_name.lower().strip()

        # Exact match
        if name_lower in self._variant_lookup:
            entry = self._variant_lookup[name_lower]
            return {
                "pcode": entry["pcode"],
                "district": entry["name_en"],
                "province": entry["province"],
                "confidence": 1.0,
            }

        # Partial match
        for variant, entry in self._variant_lookup.items():
            if name_lower in variant or variant in name_lower:
                return {
                    "pcode": entry["pcode"],
                    "district": entry["name_en"],
                    "province": entry["province"],
                    "confidence": 0.7,
                }

        return None

    def parse_article(self, article: dict[str, Any]) -> dict[str, Any]:
        """Parse a complete news article through the NLP pipeline."""
        title = article.get("title", "")
        body = article.get("full_text", "")
        text = f"{title}\n\n{body}"

        locations = self.extract_locations(text)
        temporal = self.extract_temporal(text)
        crime_type, confidence = self.classify_crime_type(text)
        victim_info = self.extract_victim_info(text)
        perp_info = self.extract_perpetrator_info(text)

        # Geocode best location
        district_pcode = None
        best_location = None
        for loc in locations:
            if loc.get("pcode"):
                district_pcode = loc["pcode"]
                best_location = loc
                break
            geocoded = self.geocode_location(loc["name"])
            if geocoded:
                district_pcode = geocoded["pcode"]
                best_location = {**loc, **geocoded}
                break

        return {
            "article_url": article.get("url"),
            "published_date": article.get("published_date"),
            "locations": locations,
            "district_pcode": district_pcode,
            "best_location": best_location,
            "incident_date": temporal.get("incident_date_raw"),
            "crime_type": crime_type,
            "crime_confidence": confidence,
            "victim_count": victim_info.get("victim_count"),
            "victim_age": victim_info.get("victim_age"),
            "victim_gender": victim_info.get("victim_gender"),
            "is_minor": victim_info.get("is_minor"),
            "perpetrator_info": perp_info,
            "confidence": confidence,
        }

    def parse_batch(
        self, articles: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Parse a batch of news articles."""
        if self.nlp_model is None:
            self.load_nlp_model()
        if not self._variant_lookup:
            self.load_gazetteer()

        results: list[dict[str, Any]] = []
        for article in articles:
            try:
                result = self.parse_article(article)
                results.append(result)
            except Exception as exc:
                logger.error("Error parsing article %s: %s", article.get("url", "?"), exc)

        return results
