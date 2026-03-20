"""Dashboard analytics API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.incidents import Incident
from app.models.boundaries import Boundary
from app.models.news_articles import DataSource
from app.models.tip_report import TipReportAnnual
from app.schemas.dashboard import (
    CaseTypeBreakdownItem,
    ConvictionRatePoint,
    DashboardSummary,
    ProvinceComparisonItem,
    TrendDataPoint,
)

router = APIRouter()


@router.get("/trends", response_model=list[TrendDataPoint])
async def get_trends(
    source: str | None = Query(default=None, description="Filter by source_type"),
    years: str | None = Query(default=None, description="Comma-separated years, e.g. 2018,2019,2020"),
    db: AsyncSession = Depends(get_db),
) -> list[TrendDataPoint]:
    """Return incident count trends over time."""
    stmt = select(
        Incident.year,
        func.count().label("count"),
        Incident.source_type,
    ).where(Incident.year.isnot(None))

    if source is not None:
        stmt = stmt.where(Incident.source_type == source)

    if years is not None:
        year_list = [int(y.strip()) for y in years.split(",") if y.strip().isdigit()]
        if year_list:
            stmt = stmt.where(Incident.year.in_(year_list))

    stmt = stmt.group_by(Incident.year, Incident.source_type).order_by(Incident.year)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        TrendDataPoint(year=row.year, count=row.count, source=row.source_type)
        for row in rows
    ]


@router.get("/province-comparison", response_model=list[ProvinceComparisonItem])
async def get_province_comparison(
    year: int | None = Query(default=None, description="Filter by year"),
    db: AsyncSession = Depends(get_db),
) -> list[ProvinceComparisonItem]:
    """Return incident counts and per-capita rates by province.

    Derives province from district boundary parent chain since
    incidents only have district_pcode (province_pcode is often empty).
    """
    from sqlalchemy.orm import aliased

    DistrictBoundary = aliased(Boundary)
    ProvinceBoundary = aliased(Boundary)

    stmt = select(
        ProvinceBoundary.pcode.label("province_pcode"),
        func.count().label("count"),
        ProvinceBoundary.name_en,
        ProvinceBoundary.population_total,
    ).select_from(Incident).join(
        DistrictBoundary,
        Incident.district_pcode == DistrictBoundary.pcode,
    ).join(
        ProvinceBoundary,
        DistrictBoundary.parent_pcode == ProvinceBoundary.pcode,
    ).where(
        Incident.district_pcode.isnot(None),
    )

    if year is not None:
        stmt = stmt.where(Incident.year == year)

    stmt = stmt.group_by(
        ProvinceBoundary.pcode,
        ProvinceBoundary.name_en,
        ProvinceBoundary.population_total,
    ).order_by(func.count().desc())

    result = await db.execute(stmt)
    rows = result.all()

    return [
        ProvinceComparisonItem(
            province=row.name_en,
            pcode=row.province_pcode,
            count=row.count,
            perCapita=(
                round(row.count / row.population_total * 100_000, 2)
                if row.population_total
                else None
            ),
        )
        for row in rows
    ]


@router.get("/case-types", response_model=list[CaseTypeBreakdownItem])
async def get_case_type_breakdown(
    province: str | None = Query(default=None, description="Filter by province pcode"),
    db: AsyncSession = Depends(get_db),
) -> list[CaseTypeBreakdownItem]:
    """Return distribution of incident types."""
    stmt = select(
        Incident.incident_type,
        func.count().label("count"),
    ).where(Incident.incident_type.isnot(None))

    if province is not None:
        stmt = stmt.where(Incident.province_pcode == province)

    stmt = stmt.group_by(Incident.incident_type).order_by(func.count().desc())

    result = await db.execute(stmt)
    rows = result.all()

    total = sum(row.count for row in rows)

    return [
        CaseTypeBreakdownItem(
            type=row.incident_type,
            count=row.count,
            percentage=round(row.count / total * 100, 2) if total > 0 else 0.0,
        )
        for row in rows
    ]


@router.get("/conviction-rates", response_model=list[ConvictionRatePoint])
async def get_conviction_rates(
    years: str | None = Query(default=None, description="Comma-separated years"),
    db: AsyncSession = Depends(get_db),
) -> list[ConvictionRatePoint]:
    """Return annual conviction funnel data from TIP reports."""
    stmt = select(TipReportAnnual).order_by(TipReportAnnual.year)

    if years is not None:
        year_list = [int(y.strip()) for y in years.split(",") if y.strip().isdigit()]
        if year_list:
            stmt = stmt.where(TipReportAnnual.year.in_(year_list))

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        ConvictionRatePoint(
            year=row.year,
            investigations=row.ptpa_investigations or 0,
            prosecutions=row.ptpa_prosecutions or 0,
            convictions=row.ptpa_convictions or 0,
            rate=(
                round((row.ptpa_convictions or 0) / row.ptpa_investigations * 100, 2)
                if (row.ptpa_investigations or 0) > 0
                else 0.0
            ),
        )
        for row in rows
    ]


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    """Return top-level KPI cards for the dashboard."""
    total_result = await db.execute(select(func.count()).select_from(Incident))
    total_incidents = total_result.scalar() or 0

    dist_result = await db.execute(
        select(func.count(distinct(Incident.district_pcode))).where(
            Incident.district_pcode.isnot(None)
        )
    )
    districts_with_data = dist_result.scalar() or 0

    ds_result = await db.execute(
        select(func.count()).select_from(DataSource).where(
            DataSource.is_active == True  # noqa: E712
        )
    )
    data_sources_active = ds_result.scalar() or 0

    tip_result = await db.execute(
        select(TipReportAnnual).order_by(TipReportAnnual.year.desc()).limit(1)
    )
    tip_row = tip_result.scalar_one_or_none()
    avg_conviction_rate = 0.0
    if tip_row and (tip_row.ptpa_investigations or 0) > 0:
        avg_conviction_rate = round(
            (tip_row.ptpa_convictions or 0) / tip_row.ptpa_investigations * 100, 2
        )

    last_result = await db.execute(select(func.max(Incident.created_at)))
    last_updated = last_result.scalar() or datetime.now(tz=timezone.utc)

    return DashboardSummary(
        totalIncidents=total_incidents,
        districtsWithData=districts_with_data,
        dataSourcesActive=data_sources_active,
        avgConvictionRate=avg_conviction_rate,
        lastUpdated=last_updated,
    )
