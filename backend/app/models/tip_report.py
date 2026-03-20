"""US State Department TIP Report annual model."""

from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import Base


class TipReportAnnual(Base):
    """Annual US TIP Report data for Pakistan."""

    __tablename__ = "tip_report_annual"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    year: int = Column(Integer, unique=True, nullable=False, index=True)
    tier_ranking: str | None = Column(String(20), nullable=True)

    ptpa_investigations: int | None = Column(Integer, nullable=True)
    ptpa_prosecutions: int | None = Column(Integer, nullable=True)
    ptpa_convictions: int | None = Column(Integer, nullable=True)
    ptpa_sex_trafficking_inv: int | None = Column(Integer, nullable=True)
    ptpa_forced_labor_inv: int | None = Column(Integer, nullable=True)

    ppc_investigations: int | None = Column(Integer, nullable=True)
    ppc_prosecutions: int | None = Column(Integer, nullable=True)
    ppc_convictions: int | None = Column(Integer, nullable=True)

    victims_identified: int | None = Column(Integer, nullable=True)
    victims_referred: int | None = Column(Integer, nullable=True)
    budget_allocated_pkr: float | None = Column(Float, nullable=True)

    key_findings: str | None = Column(Text, nullable=True)
    recommendations: str | None = Column(Text, nullable=True)

    named_hotspots = Column(ARRAY(Text), nullable=True)
    source_url: str | None = Column(Text, nullable=True)
