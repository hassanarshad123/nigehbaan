"""Court judgment model."""

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
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import Base


class CourtJudgment(Base):
    """A court judgment related to trafficking or child abuse."""

    __tablename__ = "court_judgments"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    court_name: str | None = Column(String(100), nullable=True, index=True)
    court_bench: str | None = Column(String(100), nullable=True)
    case_number: str | None = Column(String(100), nullable=True, index=True)
    judgment_date: date | None = Column(Date, nullable=True, index=True)
    judge_names = Column(ARRAY(Text), nullable=True)

    appellant: str | None = Column(Text, nullable=True)
    respondent: str | None = Column(Text, nullable=True)

    ppc_sections = Column(ARRAY(Text), nullable=True)
    statutes = Column(ARRAY(Text), nullable=True)

    is_trafficking_related: bool | None = Column(Boolean, nullable=True)
    trafficking_type: str | None = Column(String(100), nullable=True)

    incident_district_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
        index=True,
    )
    court_district_pcode: str | None = Column(
        String(20),
        ForeignKey("boundaries.pcode"),
        nullable=True,
    )

    verdict: str | None = Column(String(50), nullable=True)
    sentence: str | None = Column(Text, nullable=True)
    sentence_years: float | None = Column(Float, nullable=True)

    judgment_text: str | None = Column(Text, nullable=True)
    pdf_url: str | None = Column(Text, nullable=True)
    source_url: str | None = Column(Text, nullable=True)

    nlp_confidence: float | None = Column(Float, nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
