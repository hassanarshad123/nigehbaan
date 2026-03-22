"""Pydantic schemas for news article endpoints."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class NewsArticleListItem(BaseModel):
    """Summary of a news article for list views."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    title: str | None = None
    source_name: str | None = Field(default=None, alias="sourceName")
    published_date: date | None = Field(default=None, alias="publishedDate")
    snippet: str | None = None
    is_trafficking_relevant: bool | None = Field(default=None, alias="isTraffickingRelevant")
    extracted_locations: list | None = Field(default=None, alias="extractedLocations")


class NewsArticleDetail(BaseModel):
    """Full news article with all extracted data."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    title: str | None = None
    source_name: str | None = Field(default=None, alias="sourceName")
    url: str
    published_date: date | None = Field(default=None, alias="publishedDate")
    full_text: str | None = Field(default=None, alias="fullText")
    is_trafficking_relevant: bool | None = Field(default=None, alias="isTraffickingRelevant")
    relevance_score: float | None = Field(default=None, alias="relevanceScore")
    extracted_incidents: list | None = Field(default=None, alias="extractedIncidents")
    extracted_locations: list | None = Field(default=None, alias="extractedLocations")
    extracted_entities: list | None = Field(default=None, alias="extractedEntities")
    created_at: datetime = Field(..., alias="createdAt")
