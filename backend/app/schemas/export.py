"""Pydantic schemas for data export endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class ExportParams(BaseModel):
    """Parameters for a data export request."""

    model_config = {"frozen": True}

    table: str = Field(
        ...,
        description="Target table name: incidents, court_judgments, brick_kilns, etc.",
    )
    format: str = Field(
        default="csv",
        description="Export format: csv or geojson",
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value filters applied to the query",
    )
