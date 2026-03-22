"""Public report submission and status API endpoints."""

import hashlib
import logging
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import Path as FastPath
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.public_reports import PublicReport
from app.schemas.reports import (
    ReportCreate,
    ReportListItem,
    ReportResponse,
    ReportStatus,
    ReportUpdate,
)
from app.services.geocoder import PakistanGeocoder
from app.services.s3_upload import upload_base64_image

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazily initialised geocoder — loaded on first report submission.
_geocoder: PakistanGeocoder | None = None

_GAZETTEER_PATH = str(
    Path(__file__).resolve().parents[4]
    / "data" / "config" / "gazetteer" / "pakistan_districts.json"
)


def _get_geocoder() -> PakistanGeocoder:
    global _geocoder
    if _geocoder is None:
        _geocoder = PakistanGeocoder(gazetteer_path=_GAZETTEER_PATH)
    return _geocoder


def _reverse_geocode_district(lat: float, lon: float) -> str | None:
    """Find the nearest district pcode for given coordinates using haversine distance."""
    geocoder = _get_geocoder()
    if not geocoder.gazetteer:
        return None

    best_pcode: str | None = None
    best_dist = float("inf")
    threshold_km = 100.0

    for _name, entry in geocoder.gazetteer.items():
        entry_lat = float(entry.get("lat", 0))
        entry_lon = float(entry.get("lon", 0))
        pcode = entry.get("pcode")
        if not pcode:
            continue

        # Haversine distance in km
        dlat = math.radians(entry_lat - lat)
        dlon = math.radians(entry_lon - lon)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat))
            * math.cos(math.radians(entry_lat))
            * math.sin(dlon / 2) ** 2
        )
        dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        if dist_km < best_dist:
            best_dist = dist_km
            best_pcode = str(pcode)

    if best_dist <= threshold_km:
        return best_pcode
    return None


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
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Submit a new public report and return a reference number."""
    reference_number = f"NGB-{uuid.uuid4().hex[:8].upper()}"

    report = PublicReport(
        reference_number=reference_number,
        report_type=payload.report_type,
        description=payload.description,
        incident_date=payload.incident_date,
        address_detail=payload.address,
        photos=payload.photos,
        reporter_name=payload.reporter_name,
        reporter_contact=payload.reporter_contact,
        is_anonymous=payload.is_anonymous,
        status="pending",
        ip_hash=hashlib.sha256(
            (request.client.host if request.client else "unknown").encode()
        ).hexdigest()[:16],
    )

    # Set geometry + reverse-geocode to district
    if payload.latitude is not None and payload.longitude is not None:
        report.geometry = WKTElement(
            f"POINT({payload.longitude} {payload.latitude})", srid=4326
        )
        pcode = _reverse_geocode_district(payload.latitude, payload.longitude)
        if pcode:
            report.district_pcode = pcode

    # Text-based district matching fallback
    if report.district_pcode is None and payload.address:
        geocoder = _get_geocoder()
        pcode = geocoder.match_district(payload.address)
        if pcode:
            report.district_pcode = pcode

    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Upload photos to S3 (replace base64 with URLs)
    if report.photos:
        s3_urls = []
        for b64 in report.photos[:3]:  # max 3 photos
            url = upload_base64_image(b64, key_prefix=f"reports/{report.id}")
            if url:
                s3_urls.append(url)
        if s3_urls:
            report.photos = s3_urls
            await db.commit()

    return ReportResponse(
        id=report.id,
        reportType=report.report_type,
        status=report.status,
        createdAt=report.created_at or datetime.now(tz=timezone.utc),
        referenceNumber=report.reference_number,
    )


@router.get("/{ref_or_id}", response_model=ReportStatus)
async def get_report_status(
    ref_or_id: str = FastPath(..., description="Report numeric ID or NGB-XXXX reference number"),
    db: AsyncSession = Depends(get_db),
) -> ReportStatus:
    """Look up current status by numeric ID or reference number."""
    if ref_or_id.isdigit():
        stmt = select(PublicReport).where(PublicReport.id == int(ref_or_id))
    else:
        stmt = select(PublicReport).where(
            PublicReport.reference_number == ref_or_id.upper()
        )

    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{ref_or_id}' not found")

    return ReportStatus(
        id=report.id,
        referenceNumber=report.reference_number,
        reportType=report.report_type,
        status=report.status,
        createdAt=report.created_at or datetime.now(tz=timezone.utc),
        referredTo=report.referred_to,
        updatedAt=report.updated_at or datetime.now(tz=timezone.utc),
    )


_VALID_STATUSES = {"pending", "under_review", "verified", "rejected"}


@router.patch("/{report_id}", response_model=ReportStatus)
async def update_report_status(
    payload: ReportUpdate,
    report_id: int = FastPath(..., ge=1, description="Report ID"),
    db: AsyncSession = Depends(get_db),
) -> ReportStatus:
    """Update the status of a report (admin moderation)."""
    if payload.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{payload.status}'. "
            f"Must be one of: {', '.join(sorted(_VALID_STATUSES))}",
        )

    result = await db.execute(
        select(PublicReport).where(PublicReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    report.status = payload.status
    if payload.referred_to is not None:
        report.referred_to = payload.referred_to

    await db.commit()
    await db.refresh(report)

    return ReportStatus(
        id=report.id,
        referenceNumber=report.reference_number,
        reportType=report.report_type,
        status=report.status,
        createdAt=report.created_at or datetime.now(tz=timezone.utc),
        referredTo=report.referred_to,
        updatedAt=report.updated_at or datetime.now(tz=timezone.utc),
    )
