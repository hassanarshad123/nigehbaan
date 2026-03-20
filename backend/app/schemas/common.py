"""Common Pydantic schemas shared across the API."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    model_config = {"frozen": True}

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=25, ge=1, le=200, description="Items per page")

    @property
    def offset(self) -> int:
        """SQL OFFSET derived from page and page_size."""
        return (self.page - 1) * self.page_size


class GeoJSONGeometry(BaseModel):
    """GeoJSON Geometry object."""

    model_config = {"frozen": True}

    type: str = Field(..., description="Geometry type, e.g. Point, MultiPolygon")
    coordinates: Any = Field(..., description="Coordinate array matching the geometry type")


class GeoJSONProperties(BaseModel):
    """Arbitrary properties bag for a GeoJSON Feature."""

    model_config = {"extra": "allow"}


class GeoJSONFeature(BaseModel):
    """A single GeoJSON Feature."""

    model_config = {"frozen": True}

    type: str = Field(default="Feature")
    geometry: GeoJSONGeometry | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    id: str | int | None = None


class GeoJSONFeatureCollection(BaseModel):
    """A GeoJSON FeatureCollection."""

    model_config = {"frozen": True}

    type: str = Field(default="FeatureCollection")
    features: list[GeoJSONFeature] = Field(default_factory=list)


class APIResponse(BaseModel, Generic[T]):
    """Generic API envelope wrapping data, error, and metadata."""

    model_config = {"frozen": True}

    success: bool = True
    data: T | None = None
    error: str | None = None
    meta: dict[str, Any] | None = None
