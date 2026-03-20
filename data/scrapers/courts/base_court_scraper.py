"""Base court scraper with methods specific to Pakistani court portals.

Extends BaseScraper with court-specific functionality: case search,
judgment download, metadata extraction, and PPC section filtering.

PPC Sections of interest for trafficking/child abuse cases:
    - 366-A: Procuration of minor girl
    - 366-B: Importation of girl from foreign country
    - 369: Kidnapping or abducting child under ten
    - 370: Buying or disposing of any person as a slave
    - 371-A: Selling person for purposes of prostitution
    - 371-B: Buying person for purposes of prostitution
    - 377: Unnatural offences (relevant to child sexual abuse)
    - 292-A/B/C: Child pornography (added via PECA 2016)
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import logging

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# PPC sections related to trafficking and child abuse
PPC_SECTIONS_OF_INTEREST: list[str] = [
    "366-A",
    "366-B",
    "369",
    "370",
    "371-A",
    "371-B",
    "377",
    "292-A",
    "292-B",
    "292-C",
]

# Regex pattern matching PPC section references in text
# Matches: "section 366-A", "S. 370", "u/s 371-A", "366A", "Sec. 370"
PPC_PATTERN = re.compile(
    r"(?:section|sec\.?|s\.|u/s\.?|under section)\s*"
    r"(\d{3}(?:-?[A-C])?)",
    re.IGNORECASE,
)

# Standalone pattern for just the section numbers in case listings
PPC_STANDALONE = re.compile(
    r"\b(2(?:92-?[A-C])|3(?:66-?[AB]|69|70|71-?[AB]|77))\b"
)


def normalize_ppc_section(section: str) -> str:
    """Normalize PPC section format: '366A' -> '366-A', '371a' -> '371-A'."""
    section = section.strip().upper()
    match = re.match(r"^(\d{3})(-?)([A-C])?$", section)
    if match:
        num, _, letter = match.groups()
        if letter:
            return f"{num}-{letter}"
        return num
    return section


def extract_ppc_sections(text: str) -> list[str]:
    """Extract and normalize all PPC section references from text.

    Args:
        text: Text to search for PPC section references.

    Returns:
        Sorted list of unique normalized PPC section numbers.
    """
    found = set()
    for match in PPC_PATTERN.finditer(text):
        found.add(normalize_ppc_section(match.group(1)))
    for match in PPC_STANDALONE.finditer(text):
        found.add(normalize_ppc_section(match.group(1)))
    return sorted(found)


def filter_relevant_sections(sections: list[str]) -> list[str]:
    """Filter PPC sections to only those of interest for trafficking/abuse."""
    relevant = set(PPC_SECTIONS_OF_INTEREST)
    return [s for s in sections if s in relevant]


def parse_pakistani_date(date_str: str) -> datetime | None:
    """Parse dates in various Pakistani court formats.

    Handles: DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY,
             Month DD YYYY, YYYY-MM-DD
    """
    date_str = date_str.strip()
    formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%Y-%m-%d", "%B %d, %Y", "%B %d %Y",
        "%d %B %Y", "%d %b %Y", "%d-%b-%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


class BaseCourtScraper(BaseScraper):
    """Abstract base class for court-specific scrapers.

    Extends BaseScraper with methods for searching cases,
    downloading judgments, and extracting legal metadata.

    Subclasses must implement:
        - scrape(): Full scraping pipeline
        - validate(): Record validation
        - search_cases(): Court-specific case search
        - download_judgment(): Judgment PDF download

    Attributes:
        court_name: Full name of the court.
        ppc_sections: PPC sections to search for.
    """

    court_name: str = ""
    ppc_sections: list[str] = PPC_SECTIONS_OF_INTEREST
    rate_limit_delay: float = 2.0  # More conservative for govt portals

    def __init__(self) -> None:
        super().__init__()

    async def search_cases(
        self, year: int, case_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Search court database for cases matching criteria.

        Args:
            year: Year to search (e.g., 2024).
            case_type: Optional filter by case type.

        Returns:
            List of case reference dicts.
        """
        return []

    async def download_judgment(
        self, case_ref: dict[str, Any]
    ) -> bytes | None:
        """Download judgment PDF for a given case reference.

        Args:
            case_ref: Dictionary with case_number and year.

        Returns:
            Raw PDF bytes, or None if not available.
        """
        pdf_url = case_ref.get("pdf_url")
        if not pdf_url:
            return None
        try:
            return await self.fetch_bytes(pdf_url)
        except Exception as exc:
            logger.warning(
                "[%s] Failed to download PDF for %s: %s",
                self.name, case_ref.get("case_number", "?"), exc,
            )
            return None

    async def save_judgment_pdf(
        self, case_ref: dict[str, Any], pdf_bytes: bytes
    ) -> Path:
        """Save a judgment PDF to the raw storage directory.

        Args:
            case_ref: Case reference dict with case_number and year.
            pdf_bytes: Raw PDF content.

        Returns:
            Path to the saved PDF file.
        """
        raw_dir = self.get_raw_dir() / "pdfs"
        raw_dir.mkdir(parents=True, exist_ok=True)
        case_num = case_ref.get("case_number", "unknown").replace("/", "_")
        year = case_ref.get("year", "")
        filename = f"{case_num}_{year}.pdf"
        pdf_path = raw_dir / filename
        pdf_path.write_bytes(pdf_bytes)
        logger.info("[%s] Saved judgment PDF: %s", self.name, pdf_path)
        return pdf_path

    def extract_metadata(self, case_ref: dict[str, Any]) -> dict[str, Any]:
        """Extract structured metadata from a case reference.

        Args:
            case_ref: Dictionary with raw case data from search results.

        Returns:
            Normalized dict with court metadata fields.
        """
        title = case_ref.get("title", "") or case_ref.get("parties", "")
        description = case_ref.get("description", "")
        search_text = f"{title} {description}"
        sections = extract_ppc_sections(search_text)
        relevant = filter_relevant_sections(sections)

        date_str = case_ref.get("date_decided", "")
        parsed_date = parse_pakistani_date(date_str) if date_str else None

        return {
            "court": self.court_name,
            "case_number": case_ref.get("case_number", ""),
            "year": case_ref.get("year", ""),
            "ppc_sections": relevant if relevant else sections,
            "date_decided": parsed_date.isoformat() if parsed_date else date_str,
            "parties_petitioner": case_ref.get("petitioner", ""),
            "parties_respondent": case_ref.get("respondent", ""),
            "judge_name": case_ref.get("judge", ""),
            "bench": case_ref.get("bench", ""),
            "result": case_ref.get("result", ""),
            "pdf_url": case_ref.get("pdf_url", ""),
            "source": self.name,
            "scraped_at": datetime.utcnow().isoformat(),
        }

    def filter_relevant_cases(
        self, cases: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filter cases to only those involving relevant PPC sections.

        Args:
            cases: List of case reference dicts from search_cases().

        Returns:
            Filtered list containing only cases with relevant PPC sections.
        """
        relevant_set = set(PPC_SECTIONS_OF_INTEREST)
        filtered = []
        for case in cases:
            title = case.get("title", "") or case.get("parties", "")
            description = case.get("description", "")
            search_text = f"{title} {description}"
            sections = extract_ppc_sections(search_text)
            if any(s in relevant_set for s in sections):
                case["ppc_sections_found"] = [
                    s for s in sections if s in relevant_set
                ]
                filtered.append(case)
        return filtered

    async def scrape_year_range(
        self,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search across a range of years and collect results.

        Args:
            start_year: First year to search (default: current - 3).
            end_year: Last year to search (default: current).

        Returns:
            Combined list of case records across all years.
        """
        current_year = datetime.now().year
        start = start_year or (current_year - 3)
        end = end_year or current_year

        all_cases: list[dict[str, Any]] = []
        for year in range(start, end + 1):
            try:
                cases = await self.search_cases(year)
                relevant = self.filter_relevant_cases(cases)
                logger.info(
                    "[%s] Year %d: %d cases found, %d relevant",
                    self.name, year, len(cases), len(relevant),
                )
                for case in relevant:
                    metadata = self.extract_metadata(case)
                    pdf_data = await self.download_judgment(case)
                    if pdf_data:
                        pdf_path = await self.save_judgment_pdf(case, pdf_data)
                        metadata["pdf_local_path"] = str(pdf_path)
                    all_cases.append(metadata)
            except Exception as exc:
                logger.error("[%s] Error searching year %d: %s", self.name, year, exc)
                continue

        return all_cases
