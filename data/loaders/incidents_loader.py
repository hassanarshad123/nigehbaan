"""Loader for incident data from multiple sources → incidents table."""

from datetime import date, datetime
from typing import Any

import logging

from sqlalchemy import text

from data.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


def _parse_date(value: Any) -> date | None:
    """Parse various date formats into a date object."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s[:26], fmt).date()
        except ValueError:
            continue
    # Last resort: extract YYYY-MM-DD
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class IncidentsLoader(BaseLoader):
    name = "incidents_loader"
    source_dir = "incidents"
    table_name = "incidents"

    def transform(self, raw_record: dict[str, Any]) -> dict[str, Any] | None:
        location = raw_record.get("best_location") or {}
        if isinstance(location, str):
            location = {}

        lat = (
            raw_record.get("latitude")
            or raw_record.get("lat")
            or location.get("latitude")
            or location.get("lat")
        )
        lon = (
            raw_record.get("longitude")
            or raw_record.get("lon")
            or raw_record.get("lng")
            or location.get("longitude")
            or location.get("lng")
        )

        raw_date = raw_record.get("incident_date") or raw_record.get("published_date")
        incident_date = _parse_date(raw_date)
        year = raw_record.get("year")
        if not year and incident_date:
            year = incident_date.year

        return {
            "source_type": raw_record.get("source") or raw_record.get("source_type", "news"),
            "source_url": raw_record.get("article_url") or raw_record.get("url"),
            "incident_date": incident_date,
            "year": _safe_int(year),
            "incident_type": raw_record.get("crime_type") or raw_record.get("incident_type"),
            "district_pcode": raw_record.get("district_pcode") or location.get("district_pcode"),
            "province_pcode": raw_record.get("province_pcode") or location.get("province_pcode"),
            "location_detail": raw_record.get("location_detail") or location.get("name"),
            "latitude": _safe_float(lat),
            "longitude": _safe_float(lon),
            "victim_count": _safe_int(raw_record.get("victim_count")),
            "victim_gender": raw_record.get("victim_gender"),
            "victim_age_min": _safe_int(raw_record.get("victim_age")),
            "extraction_confidence": _safe_float(raw_record.get("confidence") or raw_record.get("crime_confidence")),
        }

    def validate(self, record: dict[str, Any]) -> bool:
        # Clear district/province pcodes that don't match loaded boundaries
        # (they'll cause FK violations). Better to have NULL than to fail.
        for key in ("district_pcode", "province_pcode"):
            val = record.get(key)
            if val and not self._valid_pcodes:
                self._load_valid_pcodes()
            if val and val not in self._valid_pcodes:
                record[key] = None
        return bool(record.get("incident_type"))

    _valid_pcodes: set[str] = set()

    def _load_valid_pcodes(self) -> None:
        """Load valid pcodes from boundaries file to avoid FK violations."""
        import json
        boundaries_dir = self.raw_base_dir / "boundaries"
        for f in boundaries_dir.glob("pak_admin*.geojson"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for feat in data.get("features", []):
                    props = feat.get("properties", {})
                    for key in props:
                        if "pcode" in key.lower():
                            val = props[key]
                            if val:
                                self._valid_pcodes.add(str(val))
            except Exception:
                pass

    async def load_records(self, records: list[dict[str, Any]]) -> int:
        """Insert incident records with optional PostGIS point geometry."""
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
                    lat = record.pop("latitude", None)
                    lon = record.pop("longitude", None)
                    has_geom = lat is not None and lon is not None

                    if has_geom:
                        sql = text(
                            "INSERT INTO incidents "
                            "(source_type, source_url, incident_date, year, incident_type, "
                            "district_pcode, province_pcode, location_detail, geometry, "
                            "victim_count, victim_gender, victim_age_min, extraction_confidence) "
                            "VALUES (:source_type, :source_url, :incident_date, :year, :incident_type, "
                            ":district_pcode, :province_pcode, :location_detail, "
                            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), "
                            ":victim_count, :victim_gender, :victim_age_min, :extraction_confidence) "
                        )
                        async with session.begin_nested():
                            await session.execute(sql, {**record, "lat": lat, "lon": lon})
                    else:
                        sql = text(
                            "INSERT INTO incidents "
                            "(source_type, source_url, incident_date, year, incident_type, "
                            "district_pcode, province_pcode, location_detail, "
                            "victim_count, victim_gender, victim_age_min, extraction_confidence) "
                            "VALUES (:source_type, :source_url, :incident_date, :year, :incident_type, "
                            ":district_pcode, :province_pcode, :location_detail, "
                            ":victim_count, :victim_gender, :victim_age_min, :extraction_confidence) "
                        )
                        async with session.begin_nested():
                            await session.execute(sql, record)

                    loaded += 1
                except Exception as exc:
                    logger.error("[%s] Insert error: %s", self.name, str(exc)[:200])
                    self.error_count += 1

            await session.commit()

        logger.info("[%s] Loaded %d/%d incidents", self.name, loaded, len(records))
        return loaded
