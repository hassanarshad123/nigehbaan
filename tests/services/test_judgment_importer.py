"""Tests for the JudgmentImporter service.

These tests exercise the pure-logic helper functions and init
validation.  No external database or network access is involved.
"""

from unittest.mock import patch, MagicMock

import pytest

from app.services.judgment_importer import (
    JudgmentImporter,
    PPC_SECTION_PATTERN,
    _extract_ppc_sections,
    _extract_verdict,
    _make_async_url,
    _transform_judgment,
)


# ---------- _make_async_url ----------


def test_make_async_url_converts_scheme():
    """Should convert postgresql:// to postgresql+asyncpg://."""
    url = "postgresql://user:pass@host:5432/db"
    result = _make_async_url(url)
    assert result.startswith("postgresql+asyncpg://")
    assert "user:pass@host:5432/db" in result


def test_make_async_url_strips_sslmode():
    """Should strip the sslmode query parameter."""
    url = "postgresql://user:pass@host/db?sslmode=require"
    result = _make_async_url(url)
    assert "sslmode" not in result


def test_make_async_url_preserves_other_params():
    """Should preserve non-sslmode query parameters."""
    url = "postgresql://user:pass@host/db?sslmode=require&connect_timeout=10"
    result = _make_async_url(url)
    assert "sslmode" not in result
    assert "connect_timeout=10" in result


def test_make_async_url_no_sslmode():
    """Should work correctly when sslmode is absent."""
    url = "postgresql://user:pass@host/db"
    result = _make_async_url(url)
    assert result == "postgresql+asyncpg://user:pass@host/db"


def test_make_async_url_already_asyncpg():
    """Should not double-convert if already postgresql+asyncpg://."""
    url = "postgresql+asyncpg://user:pass@host/db"
    result = _make_async_url(url)
    # Should keep the original scheme (doesn't start with plain postgresql://)
    assert "asyncpg" in result


# ---------- PPC_SECTION_PATTERN regex ----------


def test_ppc_section_pattern_matches_section_370():
    """Should match 'section 370'."""
    assert PPC_SECTION_PATTERN.search("convicted under section 370 PPC")


def test_ppc_section_pattern_matches_section_371_a():
    """Should match 'Section 371-A'."""
    assert PPC_SECTION_PATTERN.search("Section 371-A of the Penal Code")


def test_ppc_section_pattern_matches_s_dot_364():
    """Should match 'S. 364'."""
    assert PPC_SECTION_PATTERN.search("booked under S. 364")


def test_ppc_section_pattern_no_match_unrelated():
    """Should not match unrelated section numbers."""
    assert PPC_SECTION_PATTERN.search("section 100 of the Contract Act") is None


# ---------- _extract_ppc_sections ----------


def test_extract_ppc_sections_single_match():
    """Should extract a single PPC section number."""
    result = _extract_ppc_sections("charged under section 370 PPC")
    assert "370" in result


def test_extract_ppc_sections_multiple_matches():
    """Should extract and deduplicate multiple section numbers."""
    text = "section 370 and section 371 and section 364-A of the PPC"
    result = _extract_ppc_sections(text)
    assert len(result) >= 2
    assert "370" in result
    assert "371" in result


def test_extract_ppc_sections_no_matches():
    """Should return an empty list when no PPC sections found."""
    result = _extract_ppc_sections("The weather is nice today")
    assert result == []


def test_extract_ppc_sections_none_input():
    """Should handle None input gracefully."""
    result = _extract_ppc_sections(None)
    assert result == []


def test_extract_ppc_sections_empty_string():
    """Should return empty list for empty string."""
    result = _extract_ppc_sections("")
    assert result == []


# ---------- _extract_verdict ----------


def test_extract_verdict_convicted():
    """Should detect 'convicted' verdict."""
    text = "x" * 5000 + "The accused was convicted and sentenced to 10 years."
    assert _extract_verdict(text) == "convicted"


def test_extract_verdict_acquitted():
    """Should detect 'acquitted' verdict."""
    text = "x" * 5000 + "The accused was acquitted and set free."
    assert _extract_verdict(text) == "acquitted"


def test_extract_verdict_dismissed():
    """Should detect 'dismissed' verdict."""
    text = "x" * 5000 + "The appeal was dismissed by the court."
    assert _extract_verdict(text) == "dismissed"


def test_extract_verdict_none_for_no_keywords():
    """Should return None when no verdict keywords found."""
    text = "The case is still pending hearing."
    assert _extract_verdict(text) is None


def test_extract_verdict_none_for_empty():
    """Should return None for empty text."""
    assert _extract_verdict("") is None


def test_extract_verdict_none_for_none():
    """Should return None for None input."""
    assert _extract_verdict(None) is None


# ---------- _transform_judgment ----------


def test_transform_judgment_basic():
    """Should transform a source row into a court_judgments record."""
    row = {
        "id": "abc-123",
        "citation": "Cr.A. 100/2024",
        "court_name": "Lahore High Court",
        "bench": "Division Bench",
        "judges": ["Justice A", "Justice B"],
        "judgment_date": "2024-01-15",
        "petitioner": "State",
        "respondent": "Muhammad Ali",
        "head_notes": "Section 370 PPC trafficking case",
        "full_text": "The accused was convicted and sentenced.",
        "source_url": "https://example.com/judgment/100",
        "quality_score": 0.85,
    }
    result = _transform_judgment(row)
    assert result["case_number"] == "Cr.A. 100/2024"
    assert result["court_name"] == "Lahore High Court"
    assert result["court_bench"] == "Division Bench"
    assert result["judge_names"] == ["Justice A", "Justice B"]
    assert result["judgment_date"] == "2024-01-15"
    assert result["appellant"] == "State"
    assert result["respondent"] == "Muhammad Ali"
    assert result["is_trafficking_related"] is True
    assert result["verdict"] == "convicted"
    assert result["source_url"] == "https://example.com/judgment/100"
    assert result["nlp_confidence"] == 0.85
    assert "370" in result["ppc_sections"]


def test_transform_judgment_missing_fields():
    """Should handle missing fields gracefully with None/defaults."""
    row = {}
    result = _transform_judgment(row)
    assert result["case_number"] is None
    assert result["court_name"] is None
    assert result["judge_names"] is None
    assert result["ppc_sections"] is None
    assert result["verdict"] is None
    assert result["judgment_text"] is None


def test_transform_judgment_judges_not_list():
    """Non-list judges should result in judge_names=None."""
    row = {"judges": "Justice A, Justice B"}
    result = _transform_judgment(row)
    assert result["judge_names"] is None


def test_transform_judgment_truncates_full_text():
    """Full text should be truncated to 50000 characters."""
    row = {"full_text": "x" * 60_000}
    result = _transform_judgment(row)
    assert len(result["judgment_text"]) == 50_000


# ---------- JudgmentImporter init ----------


def test_importer_init_raises_without_url():
    """JudgmentImporter should raise ValueError when no URL is configured."""
    with patch("app.services.judgment_importer.settings") as mock_settings:
        mock_settings.external_judgments_db_url = ""
        with pytest.raises(ValueError, match="EXTERNAL_JUDGMENTS_DB_URL is not configured"):
            JudgmentImporter(external_db_url=None)


def test_importer_init_with_explicit_url():
    """JudgmentImporter should accept an explicit URL."""
    url = "postgresql://user:pass@host:5432/judgments_db"
    with patch("app.services.judgment_importer.create_async_engine") as mock_engine:
        mock_engine.return_value = MagicMock()
        importer = JudgmentImporter(external_db_url=url)
        assert importer._engine is not None
        mock_engine.assert_called_once()


def test_importer_init_converts_url_to_async():
    """JudgmentImporter should convert the URL to asyncpg format."""
    url = "postgresql://user:pass@host:5432/db?sslmode=require"
    with patch("app.services.judgment_importer.create_async_engine") as mock_engine:
        mock_engine.return_value = MagicMock()
        JudgmentImporter(external_db_url=url)
        call_args = mock_engine.call_args
        async_url = call_args[0][0]
        assert async_url.startswith("postgresql+asyncpg://")
        assert "sslmode" not in async_url
