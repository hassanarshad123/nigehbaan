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


class DistrictVulnerability(BaseModel):
    """All vulnerability indicator fields for a single district-year."""

    model_config = {"frozen": True, "populate_by_name": True}

    district_pcode: str = Field(..., alias="districtPcode")
    year: int

    school_enrollment_rate: float | None = Field(default=None, alias="schoolEnrollmentRate")
    school_dropout_rate: float | None = Field(default=None, alias="schoolDropoutRate")
    out_of_school_children: int | None = Field(default=None, alias="outOfSchoolChildren")
    literacy_rate: float | None = Field(default=None, alias="literacyRate")

    poverty_headcount_ratio: float | None = Field(default=None, alias="povertyHeadcountRatio")
    food_insecurity_rate: float | None = Field(default=None, alias="foodInsecurityRate")
    child_labor_rate: float | None = Field(default=None, alias="childLaborRate")
    unemployment_rate: float | None = Field(default=None, alias="unemploymentRate")

    population_under_18: int | None = Field(default=None, alias="populationUnder18")
    birth_registration_rate: float | None = Field(default=None, alias="birthRegistrationRate")
    child_marriage_rate: float | None = Field(default=None, alias="childMarriageRate")
    refugee_population: int | None = Field(default=None, alias="refugeePopulation")

    brick_kiln_count: int | None = Field(default=None, alias="brickKilnCount")
    brick_kiln_density_per_sqkm: float | None = Field(
        default=None, alias="brickKilnDensityPerSqkm"
    )
    distance_to_border_km: float | None = Field(default=None, alias="distanceToBorderKm")
    flood_affected_pct: float | None = Field(default=None, alias="floodAffectedPct")

    trafficking_risk_score: float | None = Field(default=None, alias="traffickingRiskScore")
    source: str | None = None
