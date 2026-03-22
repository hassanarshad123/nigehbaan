"""Pakistan-specific geocoding service."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_HEADERS = {"User-Agent": "Nigehbaan/0.1 (child-trafficking-research)"}


class PakistanGeocoder:
    """Geocode locations in Pakistan using a custom gazetteer with Nominatim fallback."""

    def __init__(self, gazetteer_path: str | None = None) -> None:
        self.gazetteer: dict[str, dict] = {}
        if gazetteer_path:
            self._load_gazetteer(gazetteer_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_gazetteer(self, path: str) -> None:
        """Load a JSON gazetteer mapping place names to coordinates.

        Expected format:
        {
            "lahore": {"lat": 31.5497, "lon": 74.3436, "pcode": "PK403"},
            ...
        }
        """
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.gazetteer = {k.lower().strip(): v for k, v in data.items()}
            logger.info("Loaded gazetteer with %d entries from %s", len(self.gazetteer), path)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load gazetteer from %s: %s", path, exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def geocode(self, location_text: str) -> tuple[float, float, float] | None:
        """Return ``(lat, lon, confidence)`` for *location_text*, or ``None``.

        1. Check the local gazetteer first (confidence = 1.0).
        2. Fall back to Nominatim, restricting to Pakistan (confidence = 0.7).
        """
        key = location_text.lower().strip()

        # --- Gazetteer lookup ---
        if key in self.gazetteer:
            entry = self.gazetteer[key]
            return (float(entry["lat"]), float(entry["lon"]), 1.0)

        # --- Nominatim fallback ---
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    _NOMINATIM_URL,
                    params={
                        "q": location_text,
                        "countrycodes": "PK",
                        "format": "json",
                        "limit": 1,
                    },
                    headers=_NOMINATIM_HEADERS,
                )
                resp.raise_for_status()
                results = resp.json()
                if results:
                    hit = results[0]
                    return (float(hit["lat"]), float(hit["lon"]), 0.7)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("Nominatim geocoding failed for '%s': %s", location_text, exc)

        return None

    def match_district(self, text: str) -> str | None:
        """Match *text* to a district P-code using the gazetteer.

        Returns the P-code string or ``None`` if no match is found.
        """
        key = text.lower().strip()
        entry = self.gazetteer.get(key)
        if entry and "pcode" in entry:
            return str(entry["pcode"])

        # Substring / fuzzy fallback — iterate gazetteer looking for partial match
        for name, data in self.gazetteer.items():
            if key in name or name in key:
                if "pcode" in data:
                    return str(data["pcode"])

        return None

    def reverse_geocode_district(
        self, lat: float, lon: float, threshold_km: float = 100.0
    ) -> str | None:
        """Find the nearest district pcode for given coordinates.

        Uses haversine distance against all gazetteer entries.
        Returns ``None`` if no entry is within *threshold_km*.
        """
        if not self.gazetteer:
            return None

        best_pcode: str | None = None
        best_dist = float("inf")

        for _name, entry in self.gazetteer.items():
            pcode = entry.get("pcode")
            if not pcode:
                continue

            entry_lat = float(entry.get("lat", 0))
            entry_lon = float(entry.get("lon", 0))

            dlat = math.radians(entry_lat - lat)
            dlon = math.radians(entry_lon - lon)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat))
                * math.cos(math.radians(entry_lat))
                * math.sin(dlon / 2) ** 2
            )
            dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            if dist_km < best_dist:
                best_dist = dist_km
                best_pcode = str(pcode)

        if best_dist <= threshold_km:
            return best_pcode
        return None
