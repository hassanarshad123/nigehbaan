"""Court judgment PDF parser with NLP extraction.

Extracts structured information from Pakistani court judgment PDFs.

Priority: P1
"""

from pathlib import Path
from typing import Any
import json
import re

import logging

logger = logging.getLogger(__name__)

RELEVANT_PPC_SECTIONS: list[str] = [
    "366-A", "366-B", "369", "370", "371-A", "371-B",
    "377", "292-A", "292-B", "292-C",
]

# Regex patterns for case header extraction
CASE_NUMBER_PATTERNS = [
    re.compile(r"(Cr\.?\s*A\.?\s*(?:No\.?)?\s*\d+\s*/\s*\d{4})", re.IGNORECASE),
    re.compile(r"(W\.?\s*P\.?\s*(?:No\.?)?\s*\d+\s*/\s*\d{4})", re.IGNORECASE),
    re.compile(r"(Criminal\s+(?:Appeal|Petition|Misc)\s*(?:No\.?)?\s*\d+\s*/\s*\d{4})", re.IGNORECASE),
    re.compile(r"((?:Crl|Cr)\.\s*(?:Appeal|Pet|Misc|Rev)\.?\s*(?:No\.?)?\s*\d+\s*/\s*\d{4})", re.IGNORECASE),
]

PPC_SECTION_PATTERN = re.compile(
    r"(?:section|sec\.?|s\.|u/s\.?|under\s+section)\s*(\d{3}(?:-?[A-C])?)",
    re.IGNORECASE,
)

PPC_STANDALONE_PATTERN = re.compile(
    r"\b(2(?:92-?[A-C])|3(?:66-?[AB]|69|70|71-?[AB]|77))\b"
)

DATE_PATTERNS = [
    re.compile(r"(\d{1,2}[./\-]\d{1,2}[./\-]\d{4})"),
    re.compile(r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})", re.IGNORECASE),
    re.compile(r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,?\s*\d{4})", re.IGNORECASE),
]

AGE_PATTERNS = [
    re.compile(r"aged?\s+(\d{1,2})\s*(?:years?|yrs?)", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s*(?:years?|yrs?)\s*old", re.IGNORECASE),
    re.compile(r"minor\s+(?:girl|boy|child).*?aged?\s+(\d{1,2})", re.IGNORECASE),
]

SENTENCE_PATTERNS = [
    re.compile(r"sentenced\s+to\s+(.*?)(?:\.|$)", re.IGNORECASE),
    re.compile(r"(?:rigorous|simple)\s+imprisonment\s+(?:for\s+)?(.+?)(?:\.|$)", re.IGNORECASE),
    re.compile(r"(acquitted|appeal\s+(?:allowed|dismissed))", re.IGNORECASE),
]

DEFAULT_GAZETTEER_PATH = Path("data/config/gazetteer/pakistan_districts.json")


class CourtJudgmentParser:
    """NLP-based parser for Pakistani court judgment PDFs."""

    def __init__(self) -> None:
        self.nlp_model = None
        self._gazetteer: dict[str, str] | None = None

    def load_nlp_model(self) -> None:
        """Load the spaCy NLP model for legal NER."""
        try:
            import spacy
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("en_core_web_sm not found, NER features limited")
                self.nlp_model = None
        except ImportError:
            logger.warning("spaCy not installed, NER features disabled")
            self.nlp_model = None

    def _load_gazetteer(self) -> dict[str, str]:
        """Lazy-load the district gazetteer."""
        if self._gazetteer is not None:
            return self._gazetteer

        self._gazetteer = {}
        gaz_path = DEFAULT_GAZETTEER_PATH
        if gaz_path.exists():
            try:
                data = json.loads(gaz_path.read_text(encoding="utf-8"))
                for d in data.get("districts", []):
                    pcode = d.get("pcode", "")
                    for variant in d.get("variants", []):
                        self._gazetteer[variant.lower()] = pcode
                    self._gazetteer[d.get("name_en", "").lower()] = pcode
            except Exception as exc:
                logger.warning("Error loading gazetteer: %s", exc)

        return self._gazetteer

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract raw text from a judgment PDF."""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed")
            return ""

        text_parts: list[str] = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as exc:
            logger.error("Error extracting text from %s: %s", pdf_path, exc)

        return "\n".join(text_parts)

    def extract_case_header(self, text: str) -> dict[str, Any]:
        """Extract case header information."""
        result: dict[str, Any] = {}

        # Case number
        for pattern in CASE_NUMBER_PATTERNS:
            match = pattern.search(text[:2000])
            if match:
                result["case_number"] = match.group(1).strip()
                break

        # Date
        for pattern in DATE_PATTERNS:
            match = pattern.search(text[:3000])
            if match:
                result["date_decided"] = match.group(1).strip()
                break

        # Judge name (look for "JUSTICE", "J.", "Hon'ble")
        judge_pattern = re.compile(
            r"(?:(?:Hon(?:'ble)?|Mr\.?|Justice)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        )
        match = judge_pattern.search(text[:3000])
        if match:
            result["judge"] = match.group(1).strip()

        # Court identification
        court_patterns = {
            "Supreme Court of Pakistan": r"Supreme\s+Court",
            "Lahore High Court": r"Lahore\s+High\s+Court",
            "Sindh High Court": r"Sindh\s+High\s+Court",
            "Peshawar High Court": r"Peshawar\s+High\s+Court",
            "Balochistan High Court": r"Balochistan\s+High\s+Court",
            "Islamabad High Court": r"Islamabad\s+High\s+Court",
        }
        for court_name, pattern in court_patterns.items():
            if re.search(pattern, text[:2000], re.IGNORECASE):
                result["court"] = court_name
                break

        return result

    def extract_parties(self, text: str) -> dict[str, str]:
        """Extract petitioner and respondent names."""
        result: dict[str, str] = {}

        # Look for "Petitioner" / "Appellant" vs "Respondent" / "State"
        versus_patterns = [
            re.compile(r"(.+?)\s+(?:vs\.?|versus|v/s\.?)\s+(.+?)(?:\n|$)", re.IGNORECASE),
        ]

        for pattern in versus_patterns:
            match = pattern.search(text[:2000])
            if match:
                result["petitioner"] = match.group(1).strip()[:200]
                result["respondent"] = match.group(2).strip()[:200]
                break

        if not result:
            pet_match = re.search(r"(?:Petitioner|Appellant)\s*[:\-]\s*(.+?)(?:\n|$)", text[:3000], re.IGNORECASE)
            resp_match = re.search(r"(?:Respondent|State)\s*[:\-]\s*(.+?)(?:\n|$)", text[:3000], re.IGNORECASE)
            if pet_match:
                result["petitioner"] = pet_match.group(1).strip()[:200]
            if resp_match:
                result["respondent"] = resp_match.group(1).strip()[:200]

        return result

    def extract_ppc_sections(self, text: str) -> list[str]:
        """Extract PPC section citations from judgment text."""
        found: set[str] = set()

        for match in PPC_SECTION_PATTERN.finditer(text):
            section = match.group(1).strip().upper()
            # Normalize: 366A -> 366-A
            norm = re.match(r"^(\d{3})(-?)([A-C])?$", section)
            if norm:
                num, _, letter = norm.groups()
                found.add(f"{num}-{letter}" if letter else num)

        for match in PPC_STANDALONE_PATTERN.finditer(text):
            section = match.group(1).strip().upper()
            norm = re.match(r"^(\d{3})(-?)([A-C])?$", section)
            if norm:
                num, _, letter = norm.groups()
                found.add(f"{num}-{letter}" if letter else num)

        return sorted(found)

    def extract_district(self, text: str) -> str | None:
        """Extract the district where the incident occurred."""
        # Look for FIR / police station patterns
        ps_pattern = re.compile(
            r"(?:FIR|F\.I\.R\.?).*?(?:P\.?S\.?|Police\s+Station)\s+(.+?)(?:,|\.|District|$)",
            re.IGNORECASE,
        )
        match = ps_pattern.search(text)
        if match:
            ps_name = match.group(1).strip()
            # Try to match against gazetteer
            gazetteer = self._load_gazetteer()
            for variant, pcode in gazetteer.items():
                if variant in ps_name.lower():
                    return variant.title()

        # District pattern
        dist_pattern = re.compile(
            r"District\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        )
        match = dist_pattern.search(text)
        if match:
            return match.group(1).strip()

        # Use NER if available
        if self.nlp_model:
            doc = self.nlp_model(text[:5000])
            gazetteer = self._load_gazetteer()
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC"):
                    if ent.text.lower() in gazetteer:
                        return ent.text

        return None

    def extract_victim_demographics(self, text: str) -> dict[str, Any]:
        """Extract victim demographic information."""
        result: dict[str, Any] = {}

        # Age extraction
        for pattern in AGE_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    result["victim_age"] = int(match.group(1))
                except ValueError:
                    pass
                break

        # Gender detection
        text_lower = text.lower()
        female_indicators = ["girl", "daughter", "woman", "female", "she ", "her "]
        male_indicators = ["boy", "son", "male", " he ", " his "]
        female_count = sum(text_lower.count(ind) for ind in female_indicators)
        male_count = sum(text_lower.count(ind) for ind in male_indicators)
        if female_count > male_count:
            result["victim_gender"] = "female"
        elif male_count > female_count:
            result["victim_gender"] = "male"

        # Count victims
        count_pattern = re.compile(r"(\d+)\s+(?:victims?|children|minors|girls?|boys?)", re.IGNORECASE)
        match = count_pattern.search(text)
        if match:
            result["victim_count"] = int(match.group(1))
        elif "minor" in text_lower or "victim" in text_lower:
            result["victim_count"] = 1

        return result

    def extract_sentence(self, text: str) -> str | None:
        """Extract the sentence/punishment from the judgment."""
        for pattern in SENTENCE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()[:500]
        return None

    def parse_judgment(self, pdf_path: Path) -> dict[str, Any]:
        """Parse a complete court judgment PDF."""
        if self.nlp_model is None:
            self.load_nlp_model()

        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning("No text extracted from %s", pdf_path)
            return {}

        header = self.extract_case_header(text)
        parties = self.extract_parties(text)
        sections = self.extract_ppc_sections(text)
        district = self.extract_district(text)
        demographics = self.extract_victim_demographics(text)
        sentence = self.extract_sentence(text)

        return {
            "pdf_path": str(pdf_path),
            "case_number": header.get("case_number"),
            "date_decided": header.get("date_decided"),
            "court": header.get("court"),
            "judge": header.get("judge"),
            "petitioner": parties.get("petitioner"),
            "respondent": parties.get("respondent"),
            "ppc_sections": sections,
            "district_of_incident": district,
            "victim_age": demographics.get("victim_age"),
            "victim_gender": demographics.get("victim_gender"),
            "victim_count": demographics.get("victim_count"),
            "sentence": sentence,
            "is_relevant": any(
                s in RELEVANT_PPC_SECTIONS for s in sections
            ),
        }

    def parse_batch(self, pdf_dir: Path) -> list[dict[str, Any]]:
        """Parse all judgment PDFs in a directory."""
        if not pdf_dir.exists():
            logger.warning("PDF directory does not exist: %s", pdf_dir)
            return []

        results: list[dict[str, Any]] = []
        for pdf_path in sorted(pdf_dir.glob("*.pdf")):
            logger.info("Parsing judgment: %s", pdf_path.name)
            try:
                result = self.parse_judgment(pdf_path)
                if result:
                    results.append(result)
            except Exception as exc:
                logger.error("Error parsing %s: %s", pdf_path.name, exc)

        return results
