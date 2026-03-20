"""Loader for court judgment data → court_judgments table."""

from typing import Any
from data.loaders.base_loader import BaseLoader


class CourtLoader(BaseLoader):
    name = "court_loader"
    source_dir = "courts"
    table_name = "court_judgments"

    def discover_files(self, extension: str = "json") -> list:
        """Discover files across all court subdirectories."""
        from pathlib import Path
        source_dir = self.raw_base_dir
        files = []
        for court_dir in ["scp", "lhc", "shc", "phc", "bhc", "ihc", "commonlii"]:
            court_path = source_dir / court_dir
            if court_path.exists():
                files.extend(sorted(
                    court_path.glob(f"*.{extension}"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                ))
        return files

    def transform(self, raw_record: dict[str, Any]) -> dict[str, Any] | None:
        case_number = raw_record.get("case_number")
        if not case_number:
            return None
        return {
            "court": raw_record.get("court"),
            "case_number": case_number,
            "year": raw_record.get("year"),
            "date_decided": raw_record.get("date_decided"),
            "parties_petitioner": raw_record.get("parties_petitioner"),
            "parties_respondent": raw_record.get("parties_respondent"),
            "ppc_sections": raw_record.get("ppc_sections", []),
            "judge_name": raw_record.get("judge_name"),
            "bench": raw_record.get("bench"),
            "result": raw_record.get("result"),
            "pdf_url": raw_record.get("pdf_url"),
        }

    def validate(self, record: dict[str, Any]) -> bool:
        return bool(record.get("case_number") and record.get("court"))
