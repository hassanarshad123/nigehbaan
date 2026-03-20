"""Legal / court judgment API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.court_judgments import CourtJudgment
from app.schemas.legal import ConvictionRateResponse, JudgmentResponse

router = APIRouter()


@router.get("/search", response_model=list[JudgmentResponse])
async def search_judgments(
    court: str | None = Query(default=None, description="Court name filter"),
    year_from: int | None = Query(default=None, alias="yearFrom", description="Start year"),
    year_to: int | None = Query(default=None, alias="yearTo", description="End year"),
    ppc_section: str | None = Query(default=None, alias="ppcSection", description="PPC section"),
    verdict: str | None = Query(default=None, description="Verdict filter"),
    district: str | None = Query(default=None, description="District pcode filter"),
    db: AsyncSession = Depends(get_db),
) -> list[JudgmentResponse]:
    """Search court judgments with optional filters."""
    stmt = select(CourtJudgment).order_by(CourtJudgment.judgment_date.desc().nullslast())

    if court is not None:
        stmt = stmt.where(CourtJudgment.court_name.ilike(f"%{court}%"))
    if year_from is not None:
        stmt = stmt.where(extract("year", CourtJudgment.judgment_date) >= year_from)
    if year_to is not None:
        stmt = stmt.where(extract("year", CourtJudgment.judgment_date) <= year_to)
    if ppc_section is not None:
        stmt = stmt.where(CourtJudgment.ppc_sections.any(ppc_section))
    if verdict is not None:
        stmt = stmt.where(CourtJudgment.verdict == verdict)
    if district is not None:
        stmt = stmt.where(CourtJudgment.incident_district_pcode == district)

    stmt = stmt.limit(100)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        JudgmentResponse(
            id=row.id,
            courtName=row.court_name,
            caseNumber=row.case_number,
            date=row.judgment_date,
            ppcSections=row.ppc_sections or [],
            verdict=row.verdict,
            sentenceYears=row.sentence_years,
            district=row.incident_district_pcode,
        )
        for row in rows
    ]


@router.get("/conviction-rates", response_model=list[ConvictionRateResponse])
async def get_conviction_rates(
    level: str | None = Query(
        default=None,
        description="Aggregation level: district, court, or year",
    ),
    db: AsyncSession = Depends(get_db),
) -> list[ConvictionRateResponse]:
    """Return conviction rate aggregations from court judgments."""
    if level == "district":
        stmt = (
            select(
                CourtJudgment.incident_district_pcode.label("group_key"),
                func.count().label("total"),
                func.count()
                .filter(CourtJudgment.verdict == "convicted")
                .label("convicted"),
            )
            .where(CourtJudgment.incident_district_pcode.isnot(None))
            .group_by(CourtJudgment.incident_district_pcode)
        )
        result = await db.execute(stmt)
        return [
            ConvictionRateResponse(
                district=row.group_key,
                investigations=row.total,
                convictions=row.convicted,
                rate=round(row.convicted / row.total * 100, 2) if row.total > 0 else 0.0,
            )
            for row in result.all()
        ]

    if level == "court":
        stmt = (
            select(
                CourtJudgment.court_name.label("group_key"),
                func.count().label("total"),
                func.count()
                .filter(CourtJudgment.verdict == "convicted")
                .label("convicted"),
            )
            .where(CourtJudgment.court_name.isnot(None))
            .group_by(CourtJudgment.court_name)
        )
        result = await db.execute(stmt)
        return [
            ConvictionRateResponse(
                court=row.group_key,
                investigations=row.total,
                convictions=row.convicted,
                rate=round(row.convicted / row.total * 100, 2) if row.total > 0 else 0.0,
            )
            for row in result.all()
        ]

    if level == "year":
        year_expr = extract("year", CourtJudgment.judgment_date)
        stmt = (
            select(
                year_expr.label("group_key"),
                func.count().label("total"),
                func.count()
                .filter(CourtJudgment.verdict == "convicted")
                .label("convicted"),
            )
            .where(CourtJudgment.judgment_date.isnot(None))
            .group_by(year_expr)
            .order_by(year_expr)
        )
        result = await db.execute(stmt)
        return [
            ConvictionRateResponse(
                year=int(row.group_key) if row.group_key else None,
                investigations=row.total,
                convictions=row.convicted,
                rate=round(row.convicted / row.total * 100, 2) if row.total > 0 else 0.0,
            )
            for row in result.all()
        ]

    # Default: overall totals
    stmt = select(
        func.count().label("total"),
        func.count()
        .filter(CourtJudgment.verdict == "convicted")
        .label("convicted"),
    ).select_from(CourtJudgment)

    result = await db.execute(stmt)
    row = result.one()
    return [
        ConvictionRateResponse(
            investigations=row.total,
            convictions=row.convicted,
            rate=round(row.convicted / row.total * 100, 2) if row.total > 0 else 0.0,
        )
    ]
