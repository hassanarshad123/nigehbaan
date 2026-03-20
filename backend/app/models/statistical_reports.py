"""Statistical reports model for NGO/government/international data."""

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
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class StatisticalReport(Base):
    """A single indicator row extracted from a PDF/HTML statistical report."""

    __tablename__ = "statistical_reports"
    __table_args__ = (
        UniqueConstraint(
            "source_name", "report_year", "indicator", "geographic_scope",
            name="uq_stat_report_source_year_indicator_geo",
        ),
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    source_name: str = Column(String(100), nullable=False, index=True)
    report_year: int | None = Column(Integer, nullable=True)
    report_title: str | None = Column(Text, nullable=True)
    indicator: str | None = Column(String(200), nullable=True)
    value: float | None = Column(Float, nullable=True)
    unit: str | None = Column(String(50), nullable=True)
    geographic_scope: str | None = Column(String(100), nullable=True)
    district_pcode: str | None = Column(String(20), nullable=True, index=True)
    victim_gender: str | None = Column(String(20), nullable=True)
    victim_age_bracket: str | None = Column(String(30), nullable=True)
    pdf_url: str | None = Column(Text, nullable=True)
    local_pdf_path: str | None = Column(Text, nullable=True)
    extraction_method: str | None = Column(String(50), nullable=True)
    extraction_confidence: float | None = Column(Float, nullable=True)
    raw_table_data = Column(JSONB, nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
