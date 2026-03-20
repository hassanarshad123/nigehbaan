"""Pydantic schemas for public reporting endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class ReportCreate(BaseModel):
    """Payload for submitting a new public report."""

    model_config = {"frozen": True, "populate_by_name": True}

    report_type: str = Field(
        ...,
        alias="reportType",
        min_length=2,
        max_length=100,
        description="Category of the report",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Free-text description of the incident",
    )
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, max_length=500)
    photos: list[str] | None = Field(default=None, description="S3 keys or URLs")
    reporter_name: str | None = Field(default=None, alias="reporterName", max_length=255)
    reporter_contact: str | None = Field(default=None, alias="reporterContact", max_length=255)
    is_anonymous: bool = Field(default=True, alias="isAnonymous")

    @model_validator(mode="after")
    def lat_lon_both_or_neither(self) -> "ReportCreate":
        """Latitude and longitude must both be present or both absent."""
        has_lat = self.latitude is not None
        has_lon = self.longitude is not None
        if has_lat != has_lon:
            raise ValueError("latitude and longitude must both be provided or both omitted")
        return self


class ReportListItem(BaseModel):
    """Summary of a public report for the admin listing."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    report_type: str = Field(..., alias="reportType")
    status: str
    district_pcode: str | None = Field(default=None, alias="districtPcode")
    created_at: datetime = Field(..., alias="createdAt")


class ReportResponse(BaseModel):
    """Response after successfully creating a public report."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    report_type: str = Field(..., alias="reportType")
    status: str
    created_at: datetime = Field(..., alias="createdAt")
    reference_number: str = Field(..., alias="referenceNumber")


class ReportStatus(BaseModel):
    """Current status of a previously submitted report."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    status: str
    referred_to: str | None = Field(default=None, alias="referredTo")
    updated_at: datetime = Field(..., alias="updatedAt")
