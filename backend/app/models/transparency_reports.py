"""Transparency reports model for tech platform CSAM/content removal data."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from app.models.base import Base


class TransparencyReport(Base):
    """A single metric from a tech platform transparency report."""

    __tablename__ = "transparency_reports"
    __table_args__ = (
        UniqueConstraint(
            "platform", "report_period", "country", "metric",
            name="uq_transparency_platform_period_country_metric",
        ),
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    platform: str = Column(String(100), nullable=False, index=True)
    report_period: str | None = Column(String(50), nullable=True)
    country: str = Column(String(100), nullable=False, default="Pakistan")
    metric: str | None = Column(String(200), nullable=True)
    value: float | None = Column(Float, nullable=True)
    unit: str | None = Column(String(50), nullable=True)
    source_url: str | None = Column(Text, nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
