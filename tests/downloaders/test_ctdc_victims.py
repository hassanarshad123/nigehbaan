"""Tests for the CTDC victims downloader (parsing, filtering, stats)."""

from pathlib import Path
from typing import Any


from data.downloaders.ctdc_victims import (
    _looks_like_csv,
    filter_pakistan_records,
    parse_ctdc_records,
    compute_summary_statistics,
)


# ---------------------------------------------------------------------------
# _looks_like_csv
# ---------------------------------------------------------------------------

class TestLooksLikeCsv:
    """Heuristic check: does text look like CSV rather than HTML/JSON?"""

    def test_empty_string(self):
        assert _looks_like_csv("") is False

    def test_html_content(self):
        assert _looks_like_csv("<html><body>hello</body></html>") is False

    def test_json_content(self):
        assert _looks_like_csv('{"key": "value"}') is False

    def test_json_array_content(self):
        assert _looks_like_csv('[{"key": "value"}]') is False

    def test_valid_csv_header(self):
        assert _looks_like_csv("col_a,col_b,col_c\n1,2,3") is True

    def test_csv_with_spaces(self):
        assert _looks_like_csv("  col_a, col_b\nval1, val2") is True


# ---------------------------------------------------------------------------
# filter_pakistan_records
# ---------------------------------------------------------------------------

class TestFilterPakistanRecords:
    """Verify filtering by Pakistan identifiers across country columns."""

    def _write_csv(self, tmp_path: Path, content: str) -> Path:
        csv_path = tmp_path / "global.csv"
        csv_path.write_text(content, encoding="utf-8")
        return csv_path

    def test_filters_by_country_of_exploitation(self, tmp_path: Path):
        csv = (
            "id,countryOfExploitation,gender\n"
            "1,Pakistan,Female\n"
            "2,India,Male\n"
            "3,Pakistan,Male\n"
        )
        csv_path = self._write_csv(tmp_path, csv)
        result_path = filter_pakistan_records(csv_path)

        import pandas as pd
        df = pd.read_csv(result_path)
        assert len(df) == 2

    def test_filters_by_citizenship_column(self, tmp_path: Path):
        csv = (
            "id,citizenship,gender\n"
            "1,PAK,Female\n"
            "2,IND,Male\n"
        )
        csv_path = self._write_csv(tmp_path, csv)
        result_path = filter_pakistan_records(csv_path)

        import pandas as pd
        df = pd.read_csv(result_path)
        assert len(df) == 1

    def test_no_country_columns_returns_original(self, tmp_path: Path):
        csv = "id,value\n1,100\n2,200\n"
        csv_path = self._write_csv(tmp_path, csv)
        result_path = filter_pakistan_records(csv_path)
        # Returns the original path when no country columns are found
        assert result_path == csv_path


# ---------------------------------------------------------------------------
# parse_ctdc_records
# ---------------------------------------------------------------------------

class TestParseCtdcRecords:
    """Verify parsing of CTDC CSV into structured dicts."""

    def _write_csv(self, tmp_path: Path, content: str) -> Path:
        csv_path = tmp_path / "ctdc.csv"
        csv_path.write_text(content, encoding="utf-8")
        return csv_path

    def test_parses_standard_columns(self, tmp_path: Path):
        csv = (
            "TypeOfTrafficking,Gender,AgeBroad,CountryOfExploitation\n"
            "Sexual,Female,0-8,Pakistan\n"
            "Labour,Male,9-17,Pakistan\n"
        )
        csv_path = self._write_csv(tmp_path, csv)
        records = parse_ctdc_records(csv_path)
        assert len(records) == 2
        assert records[0]["source"] == "CTDC"
        assert records[0]["trafficking_type"] == "Sexual"
        assert records[1]["gender"] == "Male"

    def test_empty_file_returns_empty_list(self, tmp_path: Path):
        csv_path = self._write_csv(tmp_path, "")
        records = parse_ctdc_records(csv_path)
        assert records == []

    def test_records_include_source_field(self, tmp_path: Path):
        csv = "Gender\nFemale\n"
        csv_path = self._write_csv(tmp_path, csv)
        records = parse_ctdc_records(csv_path)
        assert all(r["source"] == "CTDC" for r in records)


# ---------------------------------------------------------------------------
# compute_summary_statistics
# ---------------------------------------------------------------------------

class TestComputeSummaryStatistics:
    """Verify summary aggregation from parsed CTDC records."""

    def _make_records(self) -> list[dict[str, Any]]:
        return [
            {
                "source": "CTDC",
                "trafficking_type": "Sexual",
                "gender": "Female",
                "age_group": "0-8",
                "exploitation_type": "sexual_exploitation",
            },
            {
                "source": "CTDC",
                "trafficking_type": "Sexual",
                "gender": "Female",
                "age_group": "9-17",
                "exploitation_type": "sexual_exploitation",
            },
            {
                "source": "CTDC",
                "trafficking_type": "Labour",
                "gender": "Male",
                "age_group": "9-17",
                "exploitation_type": "forced_labour",
            },
        ]

    def test_total_victims(self):
        records = self._make_records()
        summary = compute_summary_statistics(records)
        assert summary["total_victims"] == 3

    def test_by_trafficking_type(self):
        records = self._make_records()
        summary = compute_summary_statistics(records)
        assert summary["by_trafficking_type"]["Sexual"] == 2
        assert summary["by_trafficking_type"]["Labour"] == 1

    def test_by_gender(self):
        records = self._make_records()
        summary = compute_summary_statistics(records)
        assert summary["by_gender"]["Female"] == 2
        assert summary["by_gender"]["Male"] == 1

    def test_by_age_group(self):
        records = self._make_records()
        summary = compute_summary_statistics(records)
        assert summary["by_age_group"]["0-8"] == 1
        assert summary["by_age_group"]["9-17"] == 2

    def test_empty_records(self):
        summary = compute_summary_statistics([])
        assert summary["total_victims"] == 0
        assert summary["by_trafficking_type"] == {}

    def test_missing_fields_counted_as_unknown(self):
        records = [{"source": "CTDC"}]
        summary = compute_summary_statistics(records)
        assert summary["by_trafficking_type"]["unknown"] == 1
        assert summary["by_gender"]["unknown"] == 1
