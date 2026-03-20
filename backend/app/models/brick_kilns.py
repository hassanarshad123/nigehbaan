"""Brick kiln geospatial model."""

from geoalchemy2 import Geometry
from sqlalchemy import Column, Float, ForeignKey, Integer, String

from app.models.base import Base


class BrickKiln(Base):
    """A brick kiln location with proximity metrics."""

    __tablename__ = "brick_kilns"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    geometry = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    kiln_type: str | None = Column(String(50), nullable=True)
    nearest_school_m: float | None = Column(Float, nullable=True)
    nearest_hospital_m: float | None = Column(Float, nullable=True)
    population_1km: int | None = Column(Integer, nullable=True)
    district_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
        index=True,
    )
    source: str | None = Column(String(100), nullable=True)
