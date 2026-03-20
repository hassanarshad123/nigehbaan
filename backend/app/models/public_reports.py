"""Public (citizen) report model."""

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class PublicReport(Base):
    """A report submitted by a member of the public."""

    __tablename__ = "public_reports"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    report_type: str = Column(String(100), nullable=False)
    description: str = Column(Text, nullable=False)

    geometry = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    district_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
        index=True,
    )
    address_detail: str | None = Column(Text, nullable=True)
    photos = Column(JSONB, nullable=True, comment="List of S3 keys or URLs")

    reporter_name: str | None = Column(String(255), nullable=True)
    reporter_contact: str | None = Column(String(255), nullable=True)
    is_anonymous: bool = Column(Boolean, default=True, nullable=False)

    status: str = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )
    referred_to: str | None = Column(String(255), nullable=True)
    ip_hash: str | None = Column(String(64), nullable=True)

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
