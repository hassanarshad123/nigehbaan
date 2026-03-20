"""Loader for border crossing data → border_crossings table."""

import json
from pathlib import Path
from typing import Any

import logging

from sqlalchemy import text

from data.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class BordersLoader(BaseLoader):
    name = "borders_loader"
    source_dir = "osm"
    table_name = "border_crossings"

    def discover_files(self, extension: str = "geojson") -> list[Path]:
        files = super().discover_files(extension)
        if not files:
            files = super().discover_files("json")
        return files

    def read_json(self, file_path: Path) -> list[dict[str, Any]]:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if data.get("type") == "FeatureCollection":
            return [
                {
                    **f.get("properties", {}),
                    "lat": f["geometry"]["coordinates"][1] if f.get("geometry") else None,
                    "lng": f["geometry"]["coordinates"][0] if f.get("geometry") else None,
                }
                for f in data.get("features", [])
                if f.get("geometry")
            ]
        return [data]

    def transform(self, raw_record: dict[str, Any]) -> dict[str, Any] | None:
        lat = raw_record.get("lat")
        lng = raw_record.get("lng")
        if lat is None or lng is None:
            return None
        return {
            "name": raw_record.get("name", "Unknown"),
            "latitude": float(lat),
            "longitude": float(lng),
            "border_country": raw_record.get("border_country"),
            "crossing_type": raw_record.get("crossing_type", "official"),
            "is_active": True,
        }

    def validate(self, record: dict[str, Any]) -> bool:
        lat = record.get("latitude")
        lng = record.get("longitude")
        if lat is None or lng is None:
            return False
        return 23.0 <= lat <= 37.0 and 60.0 <= lng <= 78.0

    async def load_records(self, records: list[dict[str, Any]]) -> int:
        """Insert border crossing records with PostGIS point geometry."""
        if not records:
            return 0

        try:
            from data.db import async_session_factory
        except ImportError:
            logger.warning("[%s] data.db not available", self.name)
            return 0

        loaded = 0
        async with async_session_factory() as session:
            for record in records:
                try:
                    sql = text(
                        "INSERT INTO border_crossings (name, geometry, border_country, crossing_type, is_active) "
                        "VALUES (:name, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326), "
                        ":border_country, :crossing_type, :is_active) "
                        "ON CONFLICT DO NOTHING"
                    )
                    await session.execute(sql, record)
                    loaded += 1
                except Exception as exc:
                    logger.error("[%s] Insert error for %s: %s", self.name, record.get("name"), exc)
                    self.error_count += 1

            await session.commit()

        logger.info("[%s] Loaded %d/%d border crossings", self.name, loaded, len(records))
        return loaded
