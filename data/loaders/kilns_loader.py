"""Loader for brick kiln GeoJSON data → brick_kilns table."""

import json
from pathlib import Path
from typing import Any

import logging

from sqlalchemy import text

from data.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class KilnsLoader(BaseLoader):
    name = "kilns_loader"
    source_dir = "kilns"
    table_name = "brick_kilns"

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
        lng = raw_record.get("lng") or raw_record.get("lon")
        if lat is None or lng is None:
            return None

        # Zenodo dataset properties: schools1km, hosp1km, pop1km, type, state
        nearest_school = raw_record.get("schools1km") or raw_record.get("nearest_school_m")
        nearest_hospital = raw_record.get("hosp1km") or raw_record.get("nearest_hospital_m")
        pop_1km = raw_record.get("pop1km") or raw_record.get("population_1km")
        kiln_type = raw_record.get("type") or raw_record.get("kiln_type")

        return {
            "latitude": float(lat),
            "longitude": float(lng),
            "kiln_type": kiln_type,
            "nearest_school_m": float(nearest_school) * 1000 if nearest_school and float(nearest_school) < 100 else nearest_school,
            "nearest_hospital_m": float(nearest_hospital) * 1000 if nearest_hospital and float(nearest_hospital) < 100 else nearest_hospital,
            "population_1km": int(float(pop_1km)) if pop_1km else None,
            "source": "zenodo",
        }

    def validate(self, record: dict[str, Any]) -> bool:
        lat = record.get("latitude")
        lng = record.get("longitude")
        if lat is None or lng is None:
            return False
        # Pakistan rough bounds: lat 23-37, lng 60-78
        return 23.0 <= lat <= 37.0 and 60.0 <= lng <= 78.0

    async def load_records(self, records: list[dict[str, Any]]) -> int:
        """Insert kiln records with PostGIS point geometry."""
        if not records:
            return 0

        try:
            from data.db import async_session_factory
        except ImportError:
            logger.warning("[%s] data.db not available", self.name)
            return 0

        loaded = 0
        batch_size = 500
        async with async_session_factory() as session:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                for record in batch:
                    try:
                        sql = text(
                            "INSERT INTO brick_kilns (geometry, kiln_type, nearest_school_m, nearest_hospital_m, population_1km, source) "
                            "VALUES (ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326), "
                            ":kiln_type, :nearest_school_m, :nearest_hospital_m, :population_1km, :source) "
                        )
                        await session.execute(sql, record)
                        loaded += 1
                    except Exception as exc:
                        logger.error("[%s] Insert error: %s", self.name, exc)
                        self.error_count += 1

                await session.commit()
                logger.info("[%s] Committed batch %d-%d", self.name, i, i + len(batch))

        logger.info("[%s] Loaded %d/%d kilns", self.name, loaded, len(records))
        return loaded
