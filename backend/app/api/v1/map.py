"""Map layer API endpoints — serve real data from Neon PostgreSQL."""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.border_crossings import BorderCrossing
from app.models.boundaries import Boundary
from app.models.brick_kilns import BrickKiln
from app.models.court_judgments import CourtJudgment
from app.models.incidents import Incident
from app.models.public_reports import PublicReport
from app.models.trafficking_routes import TraffickingRoute
from app.models.vulnerability import VulnerabilityIndicator
from app.schemas.common import GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONGeometry
from app.schemas.map import BorderCrossingPoint

router = APIRouter()


@router.get("/boundaries", response_model=GeoJSONFeatureCollection)
async def get_boundaries(
    level: int = Query(
        default=2, ge=0, le=5,
        description="Admin level (0=country,1=province,2=district,3=tehsil)",
    ),
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return administrative boundaries at the requested admin level as GeoJSON."""
    stmt = select(
        Boundary.id,
        Boundary.pcode,
        Boundary.name_en,
        Boundary.name_ur,
        Boundary.admin_level,
        Boundary.population_total,
        func.ST_AsGeoJSON(Boundary.geometry).label("geojson"),
    ).where(Boundary.admin_level == level)

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
        features.append(GeoJSONFeature(
            type="Feature",
            id=row.pcode,
            geometry=geometry,
            properties={
                "pcode": row.pcode,
                "nameEn": row.name_en,
                "nameUr": row.name_ur,
                "adminLevel": row.admin_level,
                "population": row.population_total,
            },
        ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get("/incidents", response_model=GeoJSONFeatureCollection)
async def get_incident_points(
    year: int | None = Query(default=None, description="Filter by year"),
    type: str | None = Query(default=None, alias="type", description="Filter by incident_type"),
    province: str | None = Query(default=None, description="Filter by province pcode"),
    geocoded_only: bool = Query(default=False, description="Only return incidents with geometry"),
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return incidents as a GeoJSON FeatureCollection.

    Geocoded incidents use their point geometry.
    Non-geocoded incidents with a district_pcode use the district centroid.
    """
    # Query incidents with their own geometry + enrichment fields
    stmt = select(
        Incident.id,
        func.ST_Y(Incident.geometry).label("lat"),
        func.ST_X(Incident.geometry).label("lon"),
        Incident.incident_type,
        Incident.sub_type,
        Incident.year,
        Incident.source_type,
        Incident.victim_count,
        Incident.victim_gender,
        Incident.victim_age_min,
        Incident.victim_age_max,
        Incident.perpetrator_type,
        Incident.fir_registered,
        Incident.conviction,
        Incident.extraction_confidence,
        Incident.district_pcode,
        Incident.location_detail,
        Boundary.name_en.label("district_name"),
    ).outerjoin(Boundary, Incident.district_pcode == Boundary.pcode)

    if geocoded_only:
        stmt = stmt.where(Incident.geometry.isnot(None))

    if year is not None:
        stmt = stmt.where(Incident.year == year)
    if type is not None:
        stmt = stmt.where(Incident.incident_type == type)
    if province is not None:
        stmt = stmt.where(Incident.province_pcode == province)

    stmt = stmt.limit(5000)

    result = await db.execute(stmt)
    rows = result.all()

    # For non-geocoded incidents, look up district centroids
    district_pcodes = {r.district_pcode for r in rows if r.district_pcode and r.lat is None}
    centroids: dict[str, tuple[float, float]] = {}
    if district_pcodes:
        centroid_stmt = select(
            Boundary.pcode,
            func.ST_Y(func.ST_Centroid(Boundary.geometry)).label("lat"),
            func.ST_X(func.ST_Centroid(Boundary.geometry)).label("lon"),
        ).where(Boundary.pcode.in_(district_pcodes))
        centroid_result = await db.execute(centroid_stmt)
        for cr in centroid_result.all():
            if cr.lat and cr.lon:
                centroids[cr.pcode] = (cr.lat, cr.lon)

    features = []
    for row in rows:
        lat = row.lat
        lon = row.lon
        if lat is None and row.district_pcode and row.district_pcode in centroids:
            lat, lon = centroids[row.district_pcode]
        if lat is None or lon is None:
            continue

        features.append(GeoJSONFeature(
            type="Feature",
            id=row.id,
            geometry=GeoJSONGeometry(
                type="Point",
                coordinates=[lon, lat],
            ),
            properties={
                "id": row.id,
                "incidentType": row.incident_type,
                "subType": row.sub_type,
                "year": row.year,
                "sourceType": row.source_type,
                "victimCount": row.victim_count,
                "victimGender": row.victim_gender,
                "victimAgeMin": row.victim_age_min,
                "victimAgeMax": row.victim_age_max,
                "perpetratorType": row.perpetrator_type,
                "firRegistered": row.fir_registered,
                "conviction": row.conviction,
                "extractionConfidence": row.extraction_confidence,
                "districtPcode": row.district_pcode,
                "districtName": row.district_name,
                "locationDetail": row.location_detail,
            },
        ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get("/kilns", response_model=GeoJSONFeatureCollection)
async def get_kiln_points(
    district: str | None = Query(default=None, description="Filter by district pcode"),
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return brick kiln locations as GeoJSON."""
    stmt = select(
        BrickKiln.id,
        func.ST_Y(BrickKiln.geometry).label("lat"),
        func.ST_X(BrickKiln.geometry).label("lon"),
        BrickKiln.kiln_type,
        BrickKiln.nearest_school_m,
        BrickKiln.population_1km,
        BrickKiln.district_pcode,
    )

    if district is not None:
        stmt = stmt.where(BrickKiln.district_pcode == district)

    stmt = stmt.limit(15000)

    result = await db.execute(stmt)
    rows = result.all()

    features = []
    for row in rows:
        features.append(GeoJSONFeature(
            type="Feature",
            id=row.id,
            geometry=GeoJSONGeometry(
                type="Point",
                coordinates=[row.lon, row.lat],
            ),
            properties={
                "id": row.id,
                "kilnType": row.kiln_type,
                "nearestSchoolM": row.nearest_school_m,
                "population1km": row.population_1km,
                "districtPcode": row.district_pcode,
            },
        ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get("/routes", response_model=GeoJSONFeatureCollection)
async def get_trafficking_routes(
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return known trafficking routes as GeoJSON LineStrings."""
    stmt = select(
        TraffickingRoute.id,
        TraffickingRoute.route_name,
        TraffickingRoute.trafficking_type,
        TraffickingRoute.confidence_level,
        TraffickingRoute.origin_country,
        TraffickingRoute.destination_country,
        func.ST_AsGeoJSON(TraffickingRoute.route_geometry).label("geojson"),
    )

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
        features.append(GeoJSONFeature(
            type="Feature",
            id=row.id,
            geometry=geometry,
            properties={
                "id": row.id,
                "routeName": row.route_name,
                "traffickingType": row.trafficking_type,
                "confidence": row.confidence_level,
                "originCountry": row.origin_country,
                "destinationCountry": row.destination_country,
            },
        ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get("/heatmap")
async def get_heatmap(
    year: int | None = Query(default=None, description="Filter by year"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return incident points as {lat, lon, weight} for heatmap rendering.

    Uses incident geometry if available, otherwise falls back to district centroid.
    """
    stmt = select(
        func.ST_Y(Incident.geometry).label("lat"),
        func.ST_X(Incident.geometry).label("lon"),
        Incident.district_pcode,
    )

    if year is not None:
        stmt = stmt.where(Incident.year == year)

    stmt = stmt.limit(10000)

    result = await db.execute(stmt)
    rows = result.all()

    # Get centroids for non-geocoded incidents
    district_pcodes = {r.district_pcode for r in rows if r.district_pcode and r.lat is None}
    centroids: dict[str, tuple[float, float]] = {}
    if district_pcodes:
        centroid_stmt = select(
            Boundary.pcode,
            func.ST_Y(func.ST_Centroid(Boundary.geometry)).label("lat"),
            func.ST_X(func.ST_Centroid(Boundary.geometry)).label("lon"),
        ).where(Boundary.pcode.in_(district_pcodes))
        centroid_result = await db.execute(centroid_stmt)
        for cr in centroid_result.all():
            if cr.lat and cr.lon:
                centroids[cr.pcode] = (cr.lat, cr.lon)

    points = []
    for row in rows:
        lat = row.lat
        lon = row.lon
        if lat is None and row.district_pcode and row.district_pcode in centroids:
            lat, lon = centroids[row.district_pcode]
        if lat is not None and lon is not None:
            points.append({"lat": lat, "lon": lon, "weight": 1.0})

    return points


@router.get("/vulnerability", response_model=GeoJSONFeatureCollection)
async def get_vulnerability_choropleth(
    year: int = Query(default=2017, description="Indicator year"),
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return district boundaries joined with vulnerability indicators as GeoJSON.

    Each feature has the district polygon geometry plus vulnerability properties
    for choropleth rendering.
    """
    stmt = select(
        Boundary.pcode,
        Boundary.name_en,
        func.ST_AsGeoJSON(Boundary.geometry).label("geojson"),
        Boundary.population_total,
        VulnerabilityIndicator.trafficking_risk_score,
        VulnerabilityIndicator.literacy_rate,
        VulnerabilityIndicator.brick_kiln_count,
        VulnerabilityIndicator.brick_kiln_density_per_sqkm,
        VulnerabilityIndicator.population_under_18,
    ).join(
        VulnerabilityIndicator,
        Boundary.pcode == VulnerabilityIndicator.district_pcode,
    ).where(
        Boundary.admin_level == 2,
        VulnerabilityIndicator.year == year,
    )

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
        features.append(GeoJSONFeature(
            type="Feature",
            id=row.pcode,
            geometry=geometry,
            properties={
                "pcode": row.pcode,
                "nameEn": row.name_en,
                "population": row.population_total,
                "traffickingRiskScore": row.trafficking_risk_score,
                "literacyRate": row.literacy_rate,
                "brickKilnCount": row.brick_kiln_count,
                "brickKilnDensity": row.brick_kiln_density_per_sqkm,
                "populationUnder18": row.population_under_18,
            },
        ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get("/borders", response_model=list[BorderCrossingPoint])
async def get_border_crossings(
    db: AsyncSession = Depends(get_db),
) -> list[BorderCrossingPoint]:
    """Return all border crossing points."""
    stmt = select(
        BorderCrossing.id,
        BorderCrossing.name,
        BorderCrossing.border_country,
        func.ST_Y(BorderCrossing.geometry).label("lat"),
        func.ST_X(BorderCrossing.geometry).label("lon"),
        BorderCrossing.vulnerability_score,
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        BorderCrossingPoint(
            id=row.id,
            name=row.name,
            border_country=row.border_country,
            lat=row.lat,
            lon=row.lon,
            vulnerability_score=row.vulnerability_score,
        )
        for row in rows
    ]


@router.get("/conviction-rates", response_model=GeoJSONFeatureCollection)
async def get_conviction_rates_choropleth(
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return per-district conviction rates as a GeoJSON choropleth.

    Computes conviction rate from court_judgments grouped by incident_district_pcode,
    joined with district boundary polygons.
    """
    # Aggregate court judgments per district
    agg_stmt = (
        select(
            CourtJudgment.incident_district_pcode.label("pcode"),
            func.count().label("total"),
            func.count().filter(CourtJudgment.verdict == "convicted").label("convicted"),
        )
        .where(CourtJudgment.incident_district_pcode.isnot(None))
        .group_by(CourtJudgment.incident_district_pcode)
    )
    agg_result = await db.execute(agg_stmt)
    agg_rows = {r.pcode: (r.total, r.convicted) for r in agg_result.all()}

    if not agg_rows:
        return GeoJSONFeatureCollection(type="FeatureCollection", features=[])

    # Fetch district boundaries for districts with judgment data
    boundary_stmt = select(
        Boundary.pcode,
        Boundary.name_en,
        func.ST_AsGeoJSON(Boundary.geometry).label("geojson"),
    ).where(
        Boundary.admin_level == 2,
        Boundary.pcode.in_(list(agg_rows.keys())),
    )
    boundary_result = await db.execute(boundary_stmt)

    features = []
    for row in boundary_result.all():
        total, convicted = agg_rows.get(row.pcode, (0, 0))
        rate = convicted / total if total > 0 else 0.0

        geometry = None
        if row.geojson:
            geom_dict = json.loads(row.geojson)
            geometry = GeoJSONGeometry(
                type=geom_dict["type"],
                coordinates=geom_dict["coordinates"],
            )
        features.append(GeoJSONFeature(
            type="Feature",
            id=row.pcode,
            geometry=geometry,
            properties={
                "pcode": row.pcode,
                "nameEn": row.name_en,
                "totalJudgments": total,
                "convicted": convicted,
                "convictionRate": round(rate, 3),
            },
        ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get("/reports", response_model=GeoJSONFeatureCollection)
async def get_public_reports_geo(
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return public reports as GeoJSON points."""
    stmt = select(
        PublicReport.id,
        func.ST_Y(PublicReport.geometry).label("lat"),
        func.ST_X(PublicReport.geometry).label("lon"),
        PublicReport.report_type,
        PublicReport.status,
        PublicReport.district_pcode,
        PublicReport.created_at,
    ).where(PublicReport.geometry.isnot(None))

    result = await db.execute(stmt)
    rows = result.all()

    # Fallback: also include reports with only a district pcode (use centroid)
    no_geo_stmt = select(
        PublicReport.id,
        PublicReport.report_type,
        PublicReport.status,
        PublicReport.district_pcode,
        PublicReport.created_at,
    ).where(
        PublicReport.geometry.is_(None),
        PublicReport.district_pcode.isnot(None),
    )
    no_geo_result = await db.execute(no_geo_stmt)
    no_geo_rows = no_geo_result.all()

    centroids: dict[str, tuple[float, float]] = {}
    if no_geo_rows:
        pcodes = {r.district_pcode for r in no_geo_rows}
        centroid_stmt = select(
            Boundary.pcode,
            func.ST_Y(func.ST_Centroid(Boundary.geometry)).label("lat"),
            func.ST_X(func.ST_Centroid(Boundary.geometry)).label("lon"),
        ).where(Boundary.pcode.in_(pcodes))
        centroid_result = await db.execute(centroid_stmt)
        for cr in centroid_result.all():
            if cr.lat and cr.lon:
                centroids[cr.pcode] = (cr.lat, cr.lon)

    features = []
    for row in rows:
        features.append(GeoJSONFeature(
            type="Feature",
            id=row.id,
            geometry=GeoJSONGeometry(type="Point", coordinates=[row.lon, row.lat]),
            properties={
                "id": row.id,
                "reportType": row.report_type,
                "status": row.status,
                "districtPcode": row.district_pcode,
                "createdAt": str(row.created_at) if row.created_at else None,
            },
        ))

    for row in no_geo_rows:
        if row.district_pcode in centroids:
            lat, lon = centroids[row.district_pcode]
            features.append(GeoJSONFeature(
                type="Feature",
                id=row.id,
                geometry=GeoJSONGeometry(type="Point", coordinates=[lon, lat]),
                properties={
                    "id": row.id,
                    "reportType": row.report_type,
                    "status": row.status,
                    "districtPcode": row.district_pcode,
                    "createdAt": str(row.created_at) if row.created_at else None,
                },
            ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get("/district-summary/{pcode}")
async def get_district_summary(
    pcode: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return a lightweight summary for the DistrictPopup overlay."""
    # Boundary info
    boundary_stmt = select(
        Boundary.name_en, Boundary.name_ur,
    ).where(Boundary.pcode == pcode)
    boundary_row = (await db.execute(boundary_stmt)).first()

    # Incident count + top types
    type_stmt = (
        select(
            Incident.incident_type,
            func.count().label("cnt"),
        )
        .where(Incident.district_pcode == pcode)
        .group_by(Incident.incident_type)
        .order_by(func.count().desc())
    )
    type_result = await db.execute(type_stmt)
    type_rows = type_result.all()

    total_incidents = sum(r.cnt for r in type_rows)
    top_types = [{"type": r.incident_type, "count": r.cnt} for r in type_rows[:5]]

    # Risk score from vulnerability indicators
    risk_stmt = select(
        VulnerabilityIndicator.trafficking_risk_score,
    ).where(VulnerabilityIndicator.district_pcode == pcode).limit(1)
    risk_row = (await db.execute(risk_stmt)).first()

    return {
        "pcode": pcode,
        "nameEn": boundary_row.name_en if boundary_row else pcode,
        "nameUr": boundary_row.name_ur if boundary_row else "",
        "incidentCount": total_incidents,
        "riskScore": risk_row.trafficking_risk_score if risk_row else None,
        "topTypes": top_types,
    }
