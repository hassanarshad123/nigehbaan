"""News article and data source models."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class NewsArticle(Base):
    """A scraped news article, potentially trafficking-related."""

    __tablename__ = "news_articles"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    source_name: str | None = Column(String(255), nullable=True, index=True)
    url: str = Column(Text, unique=True, nullable=False)
    title: str | None = Column(Text, nullable=True)
    published_date: date | None = Column(Date, nullable=True, index=True)

    extracted_incidents = Column(JSONB, nullable=True)
    extracted_locations = Column(JSONB, nullable=True)
    extracted_entities = Column(JSONB, nullable=True)

    is_trafficking_relevant: bool | None = Column(Boolean, nullable=True)
    relevance_score: float | None = Column(Float, nullable=True)
    full_text: str | None = Column(Text, nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class DataSource(Base):
    """Registry of external data sources and their scraping status."""

    __tablename__ = "data_sources"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(255), nullable=False)
    url: str | None = Column(Text, nullable=True)
    source_type: str | None = Column(String(50), nullable=True)
    priority: int | None = Column(Integer, nullable=True)

    last_scraped: datetime | None = Column(DateTime(timezone=True), nullable=True)
    last_updated: datetime | None = Column(DateTime(timezone=True), nullable=True)
    scraper_name: str | None = Column(String(100), nullable=True)
    record_count: int | None = Column(Integer, nullable=True)
    is_active: bool = Column(Boolean, default=True, nullable=False)

    notes: str | None = Column(Text, nullable=True)
