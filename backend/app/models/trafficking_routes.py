"""Trafficking route model."""

from geoalchemy2 import Geometry
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class TraffickingRoute(Base):
    """A known or suspected trafficking route."""

    __tablename__ = "trafficking_routes"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    route_name: str | None = Column(String(255), nullable=True)
    origin_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
    )
    origin_country: str | None = Column(String(100), nullable=True)
    destination_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
    )
    destination_country: str | None = Column(String(100), nullable=True)
    transit_points = Column(JSONB, nullable=True)
    route_geometry = Column(
        Geometry(geometry_type="LINESTRING", srid=4326),
        nullable=True,
    )
    trafficking_type: str | None = Column(String(100), nullable=True)
    evidence_source: str | None = Column(String(255), nullable=True)
    confidence_level: float | None = Column(Float, nullable=True)
    year_documented: int | None = Column(Integer, nullable=True)
    notes: str | None = Column(Text, nullable=True)
