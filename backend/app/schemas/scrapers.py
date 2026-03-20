"""Pydantic schemas for scraper health endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ScraperStatus(BaseModel):
    """Health status for a single data source / scraper."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    name: str
    scraper_name: str | None = Field(default=None, alias="scraperName")
    source_type: str | None = Field(default=None, alias="sourceType")
    url: str | None = None
    is_active: bool = Field(..., alias="isActive")
    last_scraped: datetime | None = Field(default=None, alias="lastScraped")
    last_updated: datetime | None = Field(default=None, alias="lastUpdated")
    record_count: int = Field(default=0, alias="recordCount")
    articles_last_24h: int = Field(default=0, alias="articlesLast24h")
    status: str  # "healthy" | "warning" | "error" | "inactive"
    schedule: str | None = None
    notes: str | None = None


class ScrapersSummary(BaseModel):
    """Aggregate KPIs across all scrapers."""

    model_config = {"frozen": True, "populate_by_name": True}

    total_scrapers: int = Field(..., alias="totalScrapers")
    active_scrapers: int = Field(..., alias="activeScrapers")
    healthy_scrapers: int = Field(..., alias="healthyScrapers")
    warning_scrapers: int = Field(..., alias="warningScrapers")
    error_scrapers: int = Field(..., alias="errorScrapers")
    total_articles: int = Field(..., alias="totalArticles")
    articles_last_24h: int = Field(..., alias="articlesLast24h")
    last_activity: datetime | None = Field(default=None, alias="lastActivity")
