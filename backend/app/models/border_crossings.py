"""Border crossing model."""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from geoalchemy2 import Geometry

from app.models.base import Base


class BorderCrossing(Base):
    """A border crossing point with vulnerability assessment."""

    __tablename__ = "border_crossings"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(255), nullable=False)
    border_country: str | None = Column(String(100), nullable=True)
    crossing_type: str | None = Column(
        String(50),
        nullable=True,
        comment="official, informal, smuggling_route",
    )
    geometry = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    is_active: bool = Column(Boolean, default=True, nullable=False)
    vulnerability_score: float | None = Column(Float, nullable=True)
    notes: str | None = Column(Text, nullable=True)
