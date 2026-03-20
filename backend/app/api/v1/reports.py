"""Public report submission and status API endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.public_reports import PublicReport
from app.schemas.reports import ReportCreate, ReportListItem, ReportResponse, ReportStatus

router = APIRouter()


@router.get("/", response_model=list[ReportListItem])
async def list_reports(
    status: str | None = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ReportListItem]:
    """List public reports with optional status filter and pagination."""
    stmt = select(PublicReport).order_by(PublicReport.created_at.desc())

    if status:
        stmt = stmt.where(PublicReport.status == status)

    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    reports = result.scalars().all()

    return [
        ReportListItem(
            id=r.id,
            reportType=r.report_type,
            status=r.status,
            districtPcode=r.district_pcode,
            createdAt=r.created_at or datetime.now(tz=timezone.utc),
        )
        for r in reports
    ]


@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Submit a new public report and return a reference number."""
    reference_number = f"NGB-{uuid.uuid4().hex[:8].upper()}"

    report = PublicReport(
        report_type=payload.report_type,
        description=payload.description,
        address_detail=payload.address,
        photos=payload.photos,
        reporter_name=payload.reporter_name,
        reporter_contact=payload.reporter_contact,
        is_anonymous=payload.is_anonymous,
        status="pending",
    )

    if payload.latitude is not None and payload.longitude is not None:
        report.geometry = WKTElement(
            f"POINT({payload.longitude} {payload.latitude})", srid=4326
        )

    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportResponse(
        id=report.id,
        reportType=report.report_type,
        status=report.status,
        createdAt=report.created_at or datetime.now(tz=timezone.utc),
        referenceNumber=reference_number,
    )


@router.get("/{report_id}", response_model=ReportStatus)
async def get_report_status(
    report_id: int = Path(..., ge=1, description="Report ID"),
    db: AsyncSession = Depends(get_db),
) -> ReportStatus:
    """Look up current status of a previously submitted report."""
    result = await db.execute(
        select(PublicReport).where(PublicReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return ReportStatus(
        id=report.id,
        status=report.status,
        referredTo=report.referred_to,
        updatedAt=report.updated_at,
    )
