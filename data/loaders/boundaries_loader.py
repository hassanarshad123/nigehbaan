"""Loader for boundary GeoJSON data → boundaries table."""

import json
from pathlib import Path
from typing import Any

import logging

from sqlalchemy import text

from data.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


def _get_prop(record: dict[str, Any], *keys: str) -> Any:
    """Get first non-None value trying both upper and lowercase keys."""
    for key in keys:
        val = record.get(key) or record.get(key.lower()) or record.get(key.upper())
        if val is not None:
            return val
    return None


class BoundariesLoader(BaseLoader):
    name = "boundaries_loader"
    source_dir = "boundaries"
    table_name = "boundaries"

    def discover_files(self, extension: str = "geojson") -> list[Path]:
        return super().discover_files(extension)

    def read_json(self, file_path: Path) -> list[dict[str, Any]]:
        """Read GeoJSON FeatureCollection into list of feature records."""
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if data.get("type") == "FeatureCollection":
            return [
                {**f.get("properties", {}), "geometry": f.get("geometry")}
                for f in data.get("features", [])
            ]
        return [data]

    def transform(self, raw_record: dict[str, Any]) -> dict[str, Any] | None:
        # HDX COD-AB uses lowercase: adm0_pcode, adm1_pcode, etc.
        # Support both upper and lowercase
        pcode = (
            _get_prop(raw_record, "adm3_pcode")
            or _get_prop(raw_record, "adm2_pcode")
            or _get_prop(raw_record, "adm1_pcode")
            or _get_prop(raw_record, "adm0_pcode")
        )
        name = (
            _get_prop(raw_record, "adm3_name", "ADM3_EN")
            or _get_prop(raw_record, "adm2_name", "ADM2_EN")
            or _get_prop(raw_record, "adm1_name", "ADM1_EN")
            or _get_prop(raw_record, "adm0_name", "ADM0_EN")
        )
        if not pcode or not name:
            return None

        # Determine admin level from which pcode field was present
        admin_level = 0
        if _get_prop(raw_record, "adm3_pcode"):
            admin_level = 3
        elif _get_prop(raw_record, "adm2_pcode"):
            admin_level = 2
        elif _get_prop(raw_record, "adm1_pcode"):
            admin_level = 1

        parent_pcode = None
        if admin_level == 3:
            parent_pcode = _get_prop(raw_record, "adm2_pcode")
        elif admin_level == 2:
            parent_pcode = _get_prop(raw_record, "adm1_pcode")
        elif admin_level == 1:
            parent_pcode = _get_prop(raw_record, "adm0_pcode")

        area_sqkm = _get_prop(raw_record, "area_sqkm")

        return {
            "pcode": pcode,
            "name_en": name,
            "name_ur": None,
            "admin_level": admin_level,
            "parent_pcode": parent_pcode,
            "area_sqkm": float(area_sqkm) if area_sqkm else None,
            "geometry": raw_record.get("geometry"),
        }

    def validate(self, record: dict[str, Any]) -> bool:
        return bool(record.get("pcode") and record.get("name_en"))

    async def load_records(self, records: list[dict[str, Any]]) -> int:
        """Insert boundary records with PostGIS geometry conversion.

        Uses ST_Multi to convert Polygon → MultiPolygon (column type).
        Each record uses a savepoint so one failure doesn't abort the batch.
        """
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
                    geom = record.pop("geometry", None)
                    geom_json = json.dumps(geom) if geom else None
                    area_sqkm = record.pop("area_sqkm", None)

                    if geom_json:
                        sql = text(
                            "INSERT INTO boundaries (pcode, name_en, name_ur, admin_level, parent_pcode, area_sqkm, geometry) "
                            "VALUES (:pcode, :name_en, :name_ur, :admin_level, :parent_pcode, :area_sqkm, "
                            "ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(CAST(:geom_json AS TEXT)), 4326))) "
                            "ON CONFLICT (pcode) DO UPDATE SET "
                            "name_en = EXCLUDED.name_en, name_ur = EXCLUDED.name_ur, "
                            "admin_level = EXCLUDED.admin_level, parent_pcode = EXCLUDED.parent_pcode, "
                            "area_sqkm = EXCLUDED.area_sqkm, geometry = EXCLUDED.geometry"
                        )
                    else:
                        sql = text(
                            "INSERT INTO boundaries (pcode, name_en, name_ur, admin_level, parent_pcode, area_sqkm) "
                            "VALUES (:pcode, :name_en, :name_ur, :admin_level, :parent_pcode, :area_sqkm) "
                            "ON CONFLICT (pcode) DO UPDATE SET "
                            "name_en = EXCLUDED.name_en, name_ur = EXCLUDED.name_ur, "
                            "admin_level = EXCLUDED.admin_level, parent_pcode = EXCLUDED.parent_pcode, "
                            "area_sqkm = EXCLUDED.area_sqkm"
                        )

                    params = {**record, "area_sqkm": area_sqkm}
                    if geom_json:
                        params["geom_json"] = geom_json

                    async with session.begin_nested():
                        await session.execute(sql, params)
                    loaded += 1
                except Exception as exc:
                    logger.error("[%s] Insert error for %s: %s", self.name, record.get("pcode"), str(exc)[:200])
                    self.error_count += 1

            await session.commit()

        logger.info("[%s] Loaded %d/%d boundaries", self.name, loaded, len(records))
        return loaded

    async def run_all_levels(self) -> dict[str, int]:
        """Load all boundary files (adm0 through adm3), loading parents first."""
        total = {"loaded": 0, "skipped": 0, "errors": 0}
        source = self.get_source_dir()

        # Load in order: country → province → district → tehsil
        for level_file in ["pak_admin0.geojson", "pak_admin1.geojson", "pak_admin2.geojson", "pak_admin3.geojson"]:
            path = source / level_file
            if path.exists():
                logger.info("[%s] Loading %s", self.name, level_file)
                self.loaded_count = 0
                self.skipped_count = 0
                self.error_count = 0
                result = await self.run(path)
                total["loaded"] += result["loaded"]
                total["skipped"] += result["skipped"]
                total["errors"] += result["errors"]
            else:
                logger.warning("[%s] File not found: %s", self.name, path)

        return total
