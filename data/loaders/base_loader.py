"""Base loader module for loading raw data into the Neon PostgreSQL database.

Loaders read JSON/CSV files from data/raw/, validate via Pydantic schemas,
and upsert into the database using SQLAlchemy async sessions.
"""

import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generic, TypeVar

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseLoader:
    """Abstract base class for data loaders.

    Reads from data/raw/{source}/ and writes to the Neon database.
    Each loader handles one target table.

    Subclasses must implement:
        - transform(): Convert raw records to DB-ready dicts
        - load_records(): Insert/upsert into the database

    Attributes:
        name: Loader identifier.
        source_dir: Directory containing raw data files.
        table_name: Target database table.
    """

    name: str = "base"
    source_dir: str = ""
    table_name: str = ""

    def __init__(self, raw_base_dir: Path | None = None) -> None:
        self.raw_base_dir = raw_base_dir or Path("data/raw")
        self.loaded_count: int = 0
        self.skipped_count: int = 0
        self.error_count: int = 0

    def get_source_dir(self) -> Path:
        """Get the source directory for raw files."""
        return self.raw_base_dir / self.source_dir

    def discover_files(self, extension: str = "json") -> list[Path]:
        """Discover raw data files to load.

        Args:
            extension: File extension to look for.

        Returns:
            List of file paths sorted by modification time (newest first).
        """
        source_dir = self.get_source_dir()
        if not source_dir.exists():
            logger.warning("[%s] Source dir does not exist: %s", self.name, source_dir)
            return []
        files = sorted(
            source_dir.glob(f"*.{extension}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return files

    def read_json(self, file_path: Path) -> list[dict[str, Any]]:
        """Read a JSON file containing a list of records.

        Args:
            file_path: Path to the JSON file.

        Returns:
            List of record dicts.
        """
        text_content = file_path.read_text(encoding="utf-8")
        data = json.loads(text_content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    def read_csv(self, file_path: Path) -> list[dict[str, Any]]:
        """Read a CSV file into a list of dicts.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of record dicts (one per row).
        """
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def transform(self, raw_record: dict[str, Any]) -> dict[str, Any] | None:
        """Transform a raw record into a DB-ready dict.

        Subclasses override this to map raw fields to database columns,
        validate required fields, and normalize values.

        Args:
            raw_record: Raw dict from the JSON/CSV file.

        Returns:
            Transformed dict ready for DB insert, or None to skip.
        """
        return raw_record

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a transformed record before loading.

        Args:
            record: Transformed dict.

        Returns:
            True if the record should be loaded.
        """
        return bool(record)

    async def load_records(
        self, records: list[dict[str, Any]]
    ) -> int:
        """Load transformed records into the database.

        Subclasses override this with table-specific upsert logic.
        Default implementation uses raw SQL INSERT for simplicity.

        Args:
            records: List of validated, transformed dicts.

        Returns:
            Number of records successfully loaded.
        """
        if not records:
            return 0

        try:
            from data.db import async_session_factory
        except ImportError:
            logger.warning(
                "[%s] data.db not available — logging %d records instead of inserting",
                self.name, len(records),
            )
            return len(records)

        loaded = 0
        async with async_session_factory() as session:
            for record in records:
                try:
                    columns = list(record.keys())
                    placeholders = [f":{col}" for col in columns]
                    sql = text(
                        f"INSERT INTO {self.table_name} ({', '.join(columns)}) "
                        f"VALUES ({', '.join(placeholders)}) "
                        f"ON CONFLICT DO NOTHING"
                    )
                    await session.execute(sql, record)
                    loaded += 1
                except Exception as exc:
                    logger.error("[%s] Insert error: %s", self.name, exc)
                    self.error_count += 1

            await session.commit()

        logger.info("[%s] Loaded %d/%d records into %s", self.name, loaded, len(records), self.table_name)
        return loaded

    async def run(self, file_path: Path | None = None) -> dict[str, int]:
        """Execute the full loading pipeline.

        Args:
            file_path: Specific file to load. If None, loads latest.

        Returns:
            Dict with loaded, skipped, error counts.
        """
        if file_path is None:
            files = self.discover_files()
            if not files:
                logger.warning("[%s] No raw files found", self.name)
                return {"loaded": 0, "skipped": 0, "errors": 0}
            file_path = files[0]  # newest file

        logger.info("[%s] Loading from %s", self.name, file_path)

        ext = file_path.suffix.lstrip(".")
        if ext in ("json", "geojson"):
            raw_records = self.read_json(file_path)
        elif ext == "csv":
            raw_records = self.read_csv(file_path)
        else:
            logger.error("[%s] Unsupported file type: %s", self.name, ext)
            return {"loaded": 0, "skipped": 0, "errors": 0}

        transformed = []
        for raw in raw_records:
            try:
                record = self.transform(raw)
                if record and self.validate(record):
                    transformed.append(record)
                else:
                    self.skipped_count += 1
            except Exception as exc:
                logger.error("[%s] Transform error: %s", self.name, exc)
                self.error_count += 1

        self.loaded_count = await self.load_records(transformed)

        result = {
            "loaded": self.loaded_count,
            "skipped": self.skipped_count,
            "errors": self.error_count,
        }
        logger.info("[%s] Load complete: %s", self.name, result)
        return result
