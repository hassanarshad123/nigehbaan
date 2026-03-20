"""Pydantic schemas for the global search endpoint."""

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result across all entity types."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    type: str = Field(..., description="Entity type: incident, judgment, article, district, etc.")
    title: str
    snippet: str | None = None
    relevance_score: float = Field(default=0.0, alias="relevanceScore")
    district_pcode: str | None = Field(default=None, alias="districtPcode")
    year: int | None = None
