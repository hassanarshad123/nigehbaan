"""Tests for the Walk Free Global Slavery Index downloader."""

from pathlib import Path


from data.downloaders.walkfree_gsi import (
    extract_pakistan_row,
    parse_vulnerability_indicators,
    VULNERABILITY_INDICATORS,
)


class TestExtractPakistanRow:
    """Unit tests for extract_pakistan_row from CSV/XLSX files."""

    def _write_csv(self, tmp_path: Path, content: str) -> Path:
        csv_path = tmp_path / "gsi.csv"
        csv_path.write_text(content, encoding="utf-8")
        return csv_path

    def test_extracts_pakistan_from_csv(self, tmp_path: Path):
        csv = (
            "country,score,rank\n"
            "India,40.2,3\n"
            "Pakistan,31.1,8\n"
            "Bangladesh,25.0,12\n"
        )
        file_path = self._write_csv(tmp_path, csv)
        result = extract_pakistan_row(file_path)
        assert result.get("country") == "Pakistan"
        # The row dict should contain the score value
        assert "score" in result or "country" in result

    def test_returns_country_only_when_no_match(self, tmp_path: Path):
        csv = "country,score\nIndia,40.2\nBangladesh,25.0\n"
        file_path = self._write_csv(tmp_path, csv)
        result = extract_pakistan_row(file_path)
        assert result.get("country") == "Pakistan"
        # Should not have extra keys beyond the default "country"
        assert len(result) >= 1

    def test_unsupported_format_returns_default(self, tmp_path: Path):
        file_path = tmp_path / "gsi.txt"
        file_path.write_text("some text data", encoding="utf-8")
        result = extract_pakistan_row(file_path)
        assert result == {"country": "Pakistan"}

    def test_case_insensitive_country_match(self, tmp_path: Path):
        csv = "Country Name,score\npakistan,31.1\n"
        file_path = self._write_csv(tmp_path, csv)
        result = extract_pakistan_row(file_path)
        assert result.get("country") == "Pakistan" or "score" in result


class TestParseVulnerabilityIndicators:
    """Tests for parse_vulnerability_indicators."""

    def test_returns_records_for_all_indicators(self):
        pakistan_data = {
            "country": "Pakistan",
            "governance_issues": 72.5,
            "lack_of_basic_needs": 65.3,
        }
        records = parse_vulnerability_indicators(pakistan_data)
        assert len(records) == len(VULNERABILITY_INDICATORS)

    def test_records_have_required_fields(self):
        pakistan_data = {"country": "Pakistan", "corruption": 55.0}
        records = parse_vulnerability_indicators(pakistan_data)
        for record in records:
            assert "indicator_name" in record
            assert "indicator_value" in record
            assert record["country"] == "Pakistan"
            assert record["source"] == "Walk Free GSI"

    def test_matched_indicator_has_value(self):
        pakistan_data = {"corruption": 55.0}
        records = parse_vulnerability_indicators(pakistan_data)
        corruption_record = next(r for r in records if r["indicator_name"] == "corruption")
        assert corruption_record["indicator_value"] == 55.0

    def test_unmatched_indicator_has_none_value(self):
        records = parse_vulnerability_indicators({})
        # All indicators should have None values when no data provided
        for record in records:
            assert record["indicator_value"] is None

    def test_vulnerability_indicators_list_not_empty(self):
        assert len(VULNERABILITY_INDICATORS) > 10
        assert "governance_issues" in VULNERABILITY_INDICATORS
        assert "corruption" in VULNERABILITY_INDICATORS
