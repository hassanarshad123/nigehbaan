"""Administrative boundary and district name variant models."""

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from geoalchemy2 import Geometry

from app.models.base import Base


class Boundary(Base):
    """Pakistan administrative boundary (province / division / district / tehsil)."""

    __tablename__ = "boundaries"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    admin_level: int = Column(Integer, nullable=False, comment="1=country,2=province,3=division,4=district,5=tehsil")
    name_en: str = Column(String(255), nullable=False)
    name_ur: str | None = Column(String(255), nullable=True)
    pcode: str = Column(String(20), unique=True, nullable=False, index=True)
    parent_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
        index=True,
    )
    geometry = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326),
        nullable=True,
    )
    population_total: int | None = Column(Integer, nullable=True)
    population_male: int | None = Column(Integer, nullable=True)
    population_female: int | None = Column(Integer, nullable=True)
    population_urban: int | None = Column(Integer, nullable=True)
    population_rural: int | None = Column(Integer, nullable=True)
    area_sqkm: float | None = Column(Float, nullable=True)


class DistrictNameVariant(Base):
    """Alternate spellings / transliterations for districts."""

    __tablename__ = "district_name_variants"
    __table_args__ = (
        UniqueConstraint("variant_name", "source", name="uq_variant_source"),
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    variant_name: str = Column(String(255), nullable=False, index=True)
    canonical_pcode: str = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=False,
        index=True,
    )
    source: str | None = Column(String(100), nullable=True)
