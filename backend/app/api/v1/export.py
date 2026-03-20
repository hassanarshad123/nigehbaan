"""Data export API endpoints."""

import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.border_crossings import BorderCrossing
from app.models.brick_kilns import BrickKiln
from app.models.court_judgments import CourtJudgment
from app.models.incidents import Incident
from app.models.news_articles import NewsArticle
from app.models.trafficking_routes import TraffickingRoute
from app.models.vulnerability import VulnerabilityIndicator
from app.schemas.common import GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONGeometry

router = APIRouter()

# Whitelisted tables for CSV export
_CSV_TABLES: dict[str, type] = {
    "incidents": Incident,
    "court_judgments": CourtJudgment,
    "news_articles": NewsArticle,
    "brick_kilns": BrickKiln,
    "vulnerability_indicators": VulnerabilityIndicator,
}

# Whitelisted tables for GeoJSON export (must have geometry)
_GEOJSON_TABLES: dict[str, dict] = {
    "incidents": {"model": Incident, "geom_col": "geometry"},
    "brick_kilns": {"model": BrickKiln, "geom_col": "geometry"},
    "trafficking_routes": {"model": TraffickingRoute, "geom_col": "route_geometry"},
    "border_crossings": {"model": BorderCrossing, "geom_col": "geometry"},
}


def _csv_value(val: object) -> str:
    """Convert a value to a CSV-safe string."""
    if val is None:
        return ""
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


@router.get("/csv")
async def export_csv(
    table: str = Query(..., description="Table to export: incidents, court_judgments, etc."),
    district: str | None = Query(default=None, description="Filter by district pcode"),
    year: int | None = Query(default=None, description="Filter by year"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export table data as a CSV download."""
    if table not in _CSV_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table '{table}'. Allowed: {', '.join(sorted(_CSV_TABLES))}",
        )

    model = _CSV_TABLES[table]

    # Select non-geometry columns only
    columns = [
        c
        for c in model.__table__.columns
        if c.name not in ("geometry", "route_geometry")
    ]
    column_names = [c.name for c in columns]

    stmt = select(*columns)

    if district is not None and hasattr(model, "district_pcode"):
        stmt = stmt.where(model.district_pcode == district)
    if year is not None and hasattr(model, "year"):
        stmt = stmt.where(model.year == year)

    stmt = stmt.limit(50000)

    result = await db.execute(stmt)
    rows = result.all()

    async def _generate():
        buf = io.StringIO()
        writer = csv.writer(buf)

        writer.writerow(column_names)
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        for row in rows:
            writer.writerow([_csv_value(getattr(row, col, None)) for col in column_names])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    return StreamingResponse(
        _generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table}_export.csv"},
    )


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
async def export_geojson(
    table: str = Query(..., description="Table to export: incidents, brick_kilns, etc."),
    district: str | None = Query(default=None, description="Filter by district pcode"),
    year: int | None = Query(default=None, description="Filter by year"),
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Export spatial data as a GeoJSON FeatureCollection."""
    if table not in _GEOJSON_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table '{table}'. Allowed: {', '.join(sorted(_GEOJSON_TABLES))}",
        )

    config = _GEOJSON_TABLES[table]
    model = config["model"]
    geom_attr = getattr(model, config["geom_col"])

    non_geom_cols = [
        c
        for c in model.__table__.columns
        if c.name != config["geom_col"]
    ]

    stmt = select(
        func.ST_AsGeoJSON(geom_attr).label("geojson"),
        *non_geom_cols,
    )

    if district is not None and hasattr(model, "district_pcode"):
        stmt = stmt.where(model.district_pcode == district)
    if year is not None:
        if hasattr(model, "year"):
            stmt = stmt.where(model.year == year)
        elif hasattr(model, "year_documented"):
            stmt = stmt.where(model.year_documented == year)

    stmt = stmt.limit(50000)

    result = await db.execute(stmt)
    rows = result.all()

    features = []
    for row in rows:
        geometry = None
        if row.geojson:
            geom_dict = json.loads(row.geojson)
            geometry = GeoJSONGeometry(
                type=geom_dict["type"],
                coordinates=geom_dict["coordinates"],
            )

        props: dict = {}
        for col in non_geom_cols:
            val = getattr(row, col.name, None)
            if val is None:
                continue
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            elif isinstance(val, (list, dict)):
                pass  # JSON-serializable as-is
            props[col.name] = val

        features.append(GeoJSONFeature(
            type="Feature",
            id=row.id,
            geometry=geometry,
            properties=props,
        ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)
