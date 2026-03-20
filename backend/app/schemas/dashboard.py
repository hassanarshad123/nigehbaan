"""Pydantic schemas for dashboard analytics endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class TrendDataPoint(BaseModel):
    """A single year's incident count for a trend line."""

    model_config = {"frozen": True}

    year: int
    count: int
    source: str | None = None


class ProvinceComparisonItem(BaseModel):
    """Per-province incident comparison row."""

    model_config = {"frozen": True, "populate_by_name": True}

    province: str
    pcode: str
    count: int
    per_capita: float | None = Field(default=None, alias="perCapita")


class CaseTypeBreakdownItem(BaseModel):
    """Case type distribution row."""

    model_config = {"frozen": True}

    type: str
    count: int
    percentage: float


class ConvictionRatePoint(BaseModel):
    """Annual conviction funnel data."""

    model_config = {"frozen": True}

    year: int
    investigations: int
    prosecutions: int
    convictions: int
    rate: float


class DashboardSummary(BaseModel):
    """Top-level KPI card data for the dashboard."""

    model_config = {"frozen": True, "populate_by_name": True}

    total_incidents: int = Field(..., alias="totalIncidents")
    districts_with_data: int = Field(..., alias="districtsWithData")
    data_sources_active: int = Field(..., alias="dataSourcesActive")
    avg_conviction_rate: float = Field(..., alias="avgConvictionRate")
    last_updated: datetime = Field(..., alias="lastUpdated")
