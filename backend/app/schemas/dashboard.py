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


class StatisticalReportItem(BaseModel):
    """A single indicator row from the statistical_reports table."""

    model_config = {"frozen": True, "populate_by_name": True}

    source_name: str = Field(..., alias="sourceName")
    report_year: int | None = Field(default=None, alias="reportYear")
    indicator: str | None = None
    value: float | None = None
    unit: str | None = None
    geographic_scope: str | None = Field(default=None, alias="geographicScope")


class TransparencyReportItem(BaseModel):
    """A single metric from tech platform transparency reports."""

    model_config = {"frozen": True, "populate_by_name": True}

    platform: str
    report_period: str | None = Field(default=None, alias="reportPeriod")
    metric: str | None = None
    value: float | None = None
    unit: str | None = None


class TipReportDetailItem(BaseModel):
    """Full TIP report detail for a single year."""

    model_config = {"frozen": True, "populate_by_name": True}

    year: int
    tier_ranking: str | None = Field(default=None, alias="tierRanking")
    ptpa_investigations: int | None = Field(default=None, alias="investigations")
    ptpa_prosecutions: int | None = Field(default=None, alias="prosecutions")
    ptpa_convictions: int | None = Field(default=None, alias="convictions")
    victims_identified: int | None = Field(default=None, alias="victimsIdentified")
    victims_referred: int | None = Field(default=None, alias="victimsReferred")
    budget_allocated_pkr: float | None = Field(default=None, alias="budgetAllocatedPkr")
    key_findings: str | None = Field(default=None, alias="keyFindings")
    named_hotspots: list[str] | None = Field(default=None, alias="namedHotspots")
