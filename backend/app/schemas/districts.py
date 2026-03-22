"""Pydantic schemas for district-related endpoints."""

from pydantic import BaseModel, Field


class DistrictListItem(BaseModel):
    """Summary row for the district listing page."""

    model_config = {"frozen": True, "populate_by_name": True}

    pcode: str
    name_en: str = Field(..., alias="nameEn")
    name_ur: str | None = Field(default=None, alias="nameUr")
    province: str | None = None
    incident_count: int = Field(default=0, alias="incidentCount")
    risk_score: float | None = Field(default=None, alias="riskScore")


class DistrictProfile(BaseModel):
    """Full district profile for the detail page."""

    model_config = {"frozen": True, "populate_by_name": True}

    pcode: str
    name_en: str = Field(..., alias="nameEn")
    name_ur: str | None = Field(default=None, alias="nameUr")
    province: str | None = None
    population: int | None = None
    incidents: int = 0
    kiln_count: int = Field(default=0, alias="kilnCount")
    vulnerability: float | None = None
    conviction_rate: float | None = Field(default=None, alias="convictionRate")
    recent_reports: int = Field(default=0, alias="recentReports")
    centroid_lat: float | None = Field(default=None, alias="centroidLat")
    centroid_lon: float | None = Field(default=None, alias="centroidLon")


class DistrictVulnerability(BaseModel):
    """All vulnerability indicator fields for a single district.

    Field aliases match the frontend TypeScript interface in api.ts.
    """

    model_config = {"frozen": True, "populate_by_name": True}

    pcode: str = Field(..., description="District P-code")
    literacy_rate: float | None = Field(default=None, alias="literacyRate")
    child_labor_rate: float | None = Field(default=None, alias="childLaborRate")
    poverty_headcount: float | None = Field(default=None, alias="povertyHeadcount")
    food_insecurity: float | None = Field(default=None, alias="foodInsecurity")
    out_of_school_rate: float | None = Field(default=None, alias="outOfSchoolRate")
    child_marriage_rate: float | None = Field(default=None, alias="childMarriageRate")
    kiln_density: float | None = Field(default=None, alias="kilnDensity")
    border_distance_km: float | None = Field(default=None, alias="borderDistanceKm")
    flood_exposure: float | None = Field(default=None, alias="floodExposure")
    enrollment_rate: float | None = Field(default=None, alias="enrollmentRate")
    incident_rate: float | None = Field(default=None, alias="incidentRate")
    conviction_rate: float | None = Field(default=None, alias="convictionRate")
    trafficking_risk_score: float | None = Field(default=None, alias="traffickingRiskScore")
