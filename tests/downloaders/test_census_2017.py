"""Tests for the Pakistan Census 2017 downloader utilities."""

from pathlib import Path

import pandas as pd

from data.downloaders.census_2017 import (
    _safe_int,
    _find_col,
    discover_csv_files,
)


class TestSafeInt:
    """Unit tests for _safe_int — safe conversion to int with commas/NaN."""

    def test_integer_string(self):
        assert _safe_int("12345") == 12345

    def test_string_with_commas(self):
        assert _safe_int("1,234,567") == 1234567

    def test_float_string(self):
        assert _safe_int("123.7") == 123

    def test_none_returns_none(self):
        assert _safe_int(None) is None

    def test_nan_float_returns_none(self):
        assert _safe_int(float("nan")) is None

    def test_nan_string_returns_none(self):
        assert _safe_int("nan") is None

    def test_none_string_returns_none(self):
        assert _safe_int("None") is None

    def test_dash_returns_none(self):
        assert _safe_int("-") is None

    def test_empty_string_returns_none(self):
        assert _safe_int("") is None

    def test_whitespace_string_returns_none(self):
        assert _safe_int("   ") is None

    def test_integer_value(self):
        assert _safe_int(42) == 42

    def test_float_value(self):
        assert _safe_int(99.9) == 99

    def test_string_with_spaces(self):
        assert _safe_int(" 1 000 ") == 1000


class TestFindCol:
    """Unit tests for _find_col — column matching by pattern."""

    def test_finds_exact_match(self):
        df = pd.DataFrame(columns=["district", "population", "male"])
        assert _find_col(df, ["district"]) == "district"

    def test_finds_substring_match(self):
        df = pd.DataFrame(columns=["District_Name", "Total_Population"])
        assert _find_col(df, ["district"]) == "District_Name"

    def test_returns_none_when_no_match(self):
        df = pd.DataFrame(columns=["col_a", "col_b"])
        assert _find_col(df, ["population", "total"]) is None

    def test_first_pattern_takes_priority(self):
        df = pd.DataFrame(columns=["area_name", "district_code"])
        # "district" pattern should match "district_code" before "area"
        result = _find_col(df, ["district", "area"])
        assert result == "district_code"

    def test_case_insensitive_matching(self):
        df = pd.DataFrame(columns=["POPULATION", "District"])
        assert _find_col(df, ["population"]) == "POPULATION"

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        assert _find_col(df, ["district"]) is None


class TestDiscoverCsvFiles:
    """Tests for discover_csv_files — finding CSVs in the census repo."""

    def test_finds_csv_files(self, tmp_path: Path):
        csv1 = tmp_path / "table1.csv"
        csv2 = tmp_path / "subdir" / "table2.csv"
        csv2.parent.mkdir()
        csv1.write_text("a,b\n1,2", encoding="utf-8")
        csv2.write_text("x,y\n3,4", encoding="utf-8")

        result = discover_csv_files(tmp_path)
        assert len(result) == 2
        assert all(p.suffix == ".csv" for p in result)

    def test_returns_empty_for_nonexistent_dir(self):
        result = discover_csv_files(Path("/nonexistent/census/repo"))
        assert result == []

    def test_ignores_non_csv_files(self, tmp_path: Path):
        (tmp_path / "readme.md").write_text("# Census")
        (tmp_path / "data.json").write_text("{}")
        (tmp_path / "actual.csv").write_text("a,b\n1,2")

        result = discover_csv_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "actual.csv"

    def test_returns_sorted_list(self, tmp_path: Path):
        (tmp_path / "z_table.csv").write_text("a\n1")
        (tmp_path / "a_table.csv").write_text("b\n2")

        result = discover_csv_files(tmp_path)
        names = [p.name for p in result]
        assert names == sorted(names)
