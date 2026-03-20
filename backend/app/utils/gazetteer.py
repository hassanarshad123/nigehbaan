"""Pakistan gazetteer loader — maps place names to coordinates and P-codes."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PakistanGazetteer:
    """Load and query a JSON gazetteer of Pakistani place names.

    Expected JSON format::

        {
            "Lahore": {
                "lat": 31.5497,
                "lon": 74.3436,
                "pcode": "PK403",
                "province_pcode": "PK4",
                "admin_level": 4
            },
            ...
        }
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self._entries: dict[str, dict[str, Any]] = {}
        if path:
            self.load(path)

    @property
    def size(self) -> int:
        """Number of entries in the gazetteer."""
        return len(self._entries)

    def load(self, path: str | Path) -> None:
        """Load the gazetteer from a JSON file.

        Keys are normalised to lowercase for case-insensitive lookup.
        """
        file_path = Path(path)
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
            self._entries = {k.lower().strip(): v for k, v in raw.items()}
            logger.info("Gazetteer loaded: %d entries from %s", len(self._entries), file_path)
        except FileNotFoundError:
            logger.error("Gazetteer file not found: %s", file_path)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON in gazetteer %s: %s", file_path, exc)

    def lookup(self, name: str) -> dict[str, Any] | None:
        """Look up a place by exact (case-insensitive) name."""
        return self._entries.get(name.lower().strip())

    def get_pcode(self, name: str) -> str | None:
        """Return the P-code for a place name, or ``None``."""
        entry = self.lookup(name)
        if entry and "pcode" in entry:
            return str(entry["pcode"])
        return None

    def get_coordinates(self, name: str) -> tuple[float, float] | None:
        """Return ``(lat, lon)`` for a place name, or ``None``."""
        entry = self.lookup(name)
        if entry and "lat" in entry and "lon" in entry:
            return (float(entry["lat"]), float(entry["lon"]))
        return None

    def search(self, query: str, limit: int = 10) -> list[tuple[str, dict[str, Any]]]:
        """Return entries whose name contains *query* (case-insensitive).

        Results are returned as ``(name, data)`` tuples, up to *limit* items.
        """
        q = query.lower().strip()
        results: list[tuple[str, dict[str, Any]]] = []
        for name, data in self._entries.items():
            if q in name:
                results.append((name, data))
                if len(results) >= limit:
                    break
        return results
