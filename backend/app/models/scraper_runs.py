"""ScraperRun model — tracks individual scraper task executions."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.models.base import Base


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_name = Column(String(100), nullable=False, index=True)
    task_id = Column(String(255), nullable=True, index=True)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, running, success, error
    started_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    records_found = Column(Integer, default=0)
    records_saved = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    triggered_by = Column(
        String(20), default="schedule"
    )  # schedule, manual, health_check
