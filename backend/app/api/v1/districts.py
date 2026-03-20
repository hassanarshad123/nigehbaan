"""District detail and listing API endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_db
from app.models.boundaries import Boundary
from app.models.brick_kilns import BrickKiln
from app.models.court_judgments import CourtJudgment
from app.models.incidents import Incident
from app.models.public_reports import PublicReport
from app.models.vulnerability import VulnerabilityIndicator
from app.schemas.common import GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONGeometry
from app.schemas.districts import DistrictListItem, DistrictProfile, DistrictVulnerability

router = APIRouter()


@router.get("/", response_model=list[DistrictListItem])
async def list_districts(
    db: AsyncSession = Depends(get_db),
) -> list[DistrictListItem]:
    """Return all districts with incident counts and risk scores."""
    # Subquery: incident count per district
    incident_sq = (
        select(
            Incident.district_pcode,
            func.count().label("incident_count"),
        )
        .where(Incident.district_pcode.isnot(None))
        .group_by(Incident.district_pcode)
        .subquery()
    )

    # Subquery: latest vulnerability score per district (DISTINCT ON)
    vuln_sq = (
        select(
            VulnerabilityIndicator.district_pcode,
            VulnerabilityIndicator.trafficking_risk_score,
        )
        .distinct(VulnerabilityIndicator.district_pcode)
        .order_by(
            VulnerabilityIndicator.district_pcode,
            VulnerabilityIndicator.year.desc(),
        )
        .subquery()
    )

    ParentBoundary = aliased(Boundary)

    stmt = (
        select(
            Boundary.pcode,
            Boundary.name_en,
            Boundary.name_ur,
            ParentBoundary.name_en.label("province_name"),
            incident_sq.c.incident_count,
            vuln_sq.c.trafficking_risk_score,
        )
        .where(Boundary.admin_level == 2)
        .outerjoin(incident_sq, Boundary.pcode == incident_sq.c.district_pcode)
        .outerjoin(vuln_sq, Boundary.pcode == vuln_sq.c.district_pcode)
        .outerjoin(ParentBoundary, Boundary.parent_pcode == ParentBoundary.pcode)
        .order_by(Boundary.name_en)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        DistrictListItem(
            pcode=row.pcode,
            nameEn=row.name_en,
            nameUr=row.name_ur,
            province=row.province_name,
            incidentCount=row.incident_count or 0,
            riskScore=row.trafficking_risk_score,
        )
        for row in rows
    ]


@router.get("/{pcode}", response_model=DistrictProfile)
async def get_district_profile(
    pcode: str = Path(..., description="District P-code, e.g. PK401"),
    db: AsyncSession = Depends(get_db),
) -> DistrictProfile:
    """Return full profile for a single district."""
    boundary_result = await db.execute(
        select(Boundary).where(Boundary.pcode == pcode)
    )
    boundary = boundary_result.scalar_one_or_none()
    if boundary is None:
        raise HTTPException(status_code=404, detail=f"District {pcode} not found")

    # Province name from parent
    province_name = None
    if boundary.parent_pcode:
        parent_result = await db.execute(
            select(Boundary.name_en).where(Boundary.pcode == boundary.parent_pcode)
        )
        province_name = parent_result.scalar_one_or_none()

    # Incident count
    inc_result = await db.execute(
        select(func.count()).select_from(Incident).where(
            Incident.district_pcode == pcode
        )
    )
    incidents = inc_result.scalar() or 0

    # Kiln count
    kiln_result = await db.execute(
        select(func.count()).select_from(BrickKiln).where(
            BrickKiln.district_pcode == pcode
        )
    )
    kiln_count = kiln_result.scalar() or 0

    # Latest vulnerability score
    vuln_result = await db.execute(
        select(VulnerabilityIndicator.trafficking_risk_score)
        .where(VulnerabilityIndicator.district_pcode == pcode)
        .order_by(VulnerabilityIndicator.year.desc())
        .limit(1)
    )
    vulnerability = vuln_result.scalar_one_or_none()

    # Conviction rate from court judgments in this district
    total_j_result = await db.execute(
        select(func.count()).select_from(CourtJudgment).where(
            CourtJudgment.incident_district_pcode == pcode
        )
    )
    total_judgments = total_j_result.scalar() or 0

    conviction_rate = None
    if total_judgments > 0:
        convicted_result = await db.execute(
            select(func.count()).select_from(CourtJudgment).where(
                CourtJudgment.incident_district_pcode == pcode,
                CourtJudgment.verdict == "convicted",
            )
        )
        convicted = convicted_result.scalar() or 0
        conviction_rate = round(convicted / total_judgments * 100, 2)

    # Recent reports
    reports_result = await db.execute(
        select(func.count()).select_from(PublicReport).where(
            PublicReport.district_pcode == pcode
        )
    )
    recent_reports = reports_result.scalar() or 0

    return DistrictProfile(
        pcode=boundary.pcode,
        nameEn=boundary.name_en,
        nameUr=boundary.name_ur,
        province=province_name,
        population=boundary.population_total,
        incidents=incidents,
        kilnCount=kiln_count,
        vulnerability=vulnerability,
        convictionRate=conviction_rate,
        recentReports=recent_reports,
    )


@router.get("/{pcode}/incidents", response_model=GeoJSONFeatureCollection)
async def get_district_incidents(
    pcode: str = Path(..., description="District P-code"),
    years: str | None = Query(default=None, description="Comma-separated years"),
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return geocoded incidents within a district as GeoJSON."""
    stmt = select(
        Incident.id,
        func.ST_Y(Incident.geometry).label("lat"),
        func.ST_X(Incident.geometry).label("lon"),
        Incident.incident_type,
        Incident.year,
        Incident.source_type,
        Incident.victim_count,
        Incident.victim_gender,
        Incident.location_detail,
    ).where(Incident.district_pcode == pcode)

    if years is not None:
        year_list = [int(y.strip()) for y in years.split(",") if y.strip().isdigit()]
        if year_list:
            stmt = stmt.where(Incident.year.in_(year_list))

    stmt = stmt.limit(5000)
    result = await db.execute(stmt)
    rows = result.all()

    # Fallback centroid for non-geocoded incidents
    centroid_stmt = select(
        func.ST_Y(func.ST_Centroid(Boundary.geometry)).label("lat"),
        func.ST_X(func.ST_Centroid(Boundary.geometry)).label("lon"),
    ).where(Boundary.pcode == pcode)
    centroid_result = await db.execute(centroid_stmt)
    centroid = centroid_result.one_or_none()
    fallback_lat = centroid.lat if centroid else None
    fallback_lon = centroid.lon if centroid else None

    features = []
    for row in rows:
        lat = row.lat
        lon = row.lon
        if lat is None and fallback_lat is not None:
            lat, lon = fallback_lat, fallback_lon
        if lat is None or lon is None:
            continue

        features.append(GeoJSONFeature(
            type="Feature",
            id=row.id,
            geometry=GeoJSONGeometry(type="Point", coordinates=[lon, lat]),
            properties={
                "id": row.id,
                "incidentType": row.incident_type,
                "year": row.year,
                "sourceType": row.source_type,
                "victimCount": row.victim_count,
                "victimGender": row.victim_gender,
                "locationDetail": row.location_detail,
            },
        ))

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get("/{pcode}/vulnerability", response_model=DistrictVulnerability)
async def get_district_vulnerability(
    pcode: str = Path(..., description="District P-code"),
    db: AsyncSession = Depends(get_db),
) -> DistrictVulnerability:
    """Return the latest vulnerability indicators for a district."""
    result = await db.execute(
        select(VulnerabilityIndicator)
        .where(VulnerabilityIndicator.district_pcode == pcode)
        .order_by(VulnerabilityIndicator.year.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No vulnerability data found for district {pcode}",
        )

    return DistrictVulnerability(
        districtPcode=row.district_pcode,
        year=row.year,
        schoolEnrollmentRate=row.school_enrollment_rate,
        schoolDropoutRate=row.school_dropout_rate,
        outOfSchoolChildren=row.out_of_school_children,
        literacyRate=row.literacy_rate,
        povertyHeadcountRatio=row.poverty_headcount_ratio,
        foodInsecurityRate=row.food_insecurity_rate,
        childLaborRate=row.child_labor_rate,
        unemploymentRate=row.unemployment_rate,
        populationUnder18=row.population_under_18,
        birthRegistrationRate=row.birth_registration_rate,
        childMarriageRate=row.child_marriage_rate,
        refugeePopulation=row.refugee_population,
        brickKilnCount=row.brick_kiln_count,
        brickKilnDensityPerSqkm=row.brick_kiln_density_per_sqkm,
        distanceToBorderKm=row.distance_to_border_km,
        floodAffectedPct=row.flood_affected_pct,
        traffickingRiskScore=row.trafficking_risk_score,
        source=row.source,
    )
