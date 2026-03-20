"""Trafficking / abuse incident model."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from geoalchemy2 import Geometry

from app.models.base import Base


class Incident(Base):
    """A single reported trafficking or child-abuse incident."""

    __tablename__ = "incidents"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    source_type: str | None = Column(
        String(50),
        nullable=True,
        comment="e.g. sahil, news, court, tip_report, public_report",
    )
    source_id: str | None = Column(String(100), nullable=True)
    source_url: str | None = Column(Text, nullable=True)

    incident_date: date | None = Column(Date, nullable=True)
    report_date: date | None = Column(Date, nullable=True)
    year: int | None = Column(Integer, nullable=True, index=True)
    month: int | None = Column(Integer, nullable=True)

    district_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
        index=True,
    )
    province_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
        index=True,
    )
    location_detail: str | None = Column(Text, nullable=True)
    geometry = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    geocode_confidence: float | None = Column(Float, nullable=True)

    incident_type: str | None = Column(String(100), nullable=True, index=True)
    sub_type: str | None = Column(String(100), nullable=True)
    victim_count: int | None = Column(Integer, nullable=True)
    victim_gender: str | None = Column(String(20), nullable=True)
    victim_age_min: int | None = Column(Integer, nullable=True)
    victim_age_max: int | None = Column(Integer, nullable=True)
    victim_age_bracket: str | None = Column(String(30), nullable=True)

    perpetrator_type: str | None = Column(String(100), nullable=True)
    perpetrator_count: int | None = Column(Integer, nullable=True)

    fir_registered: bool | None = Column(Boolean, nullable=True)
    case_status: str | None = Column(String(50), nullable=True)
    conviction: bool | None = Column(Boolean, nullable=True)
    sentence_detail: str | None = Column(Text, nullable=True)

    extraction_confidence: float | None = Column(Float, nullable=True)
    raw_text: str | None = Column(Text, nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
