"""Pydantic schemas for map-related API responses."""


from pydantic import BaseModel, Field

from app.schemas.common import GeoJSONGeometry


class BoundaryResponse(BaseModel):
    """Administrative boundary returned for the map layer."""

    model_config = {"frozen": True}

    pcode: str
    name_en: str = Field(..., alias="nameEn")
    name_ur: str | None = Field(default=None, alias="nameUr")
    admin_level: int = Field(..., alias="adminLevel")
    population: int | None = None
    geometry: GeoJSONGeometry | None = None


class IncidentMapPoint(BaseModel):
    """Lightweight incident point for map rendering."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    lat: float
    lon: float
    incident_type: str | None = Field(default=None, alias="incidentType")
    year: int | None = None
    source_type: str | None = Field(default=None, alias="sourceType")


class KilnMapPoint(BaseModel):
    """Brick kiln point for map rendering."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    lat: float
    lon: float
    kiln_type: str | None = Field(default=None, alias="kilnType")
    nearest_school_m: float | None = Field(default=None, alias="nearestSchoolM")
    population_1km: int | None = Field(default=None, alias="population1km")


class BorderCrossingPoint(BaseModel):
    """Border crossing point for map rendering."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    name: str
    border_country: str | None = Field(default=None, alias="borderCountry")
    lat: float
    lon: float
    vulnerability_score: float | None = Field(default=None, alias="vulnerabilityScore")


class RouteResponse(BaseModel):
    """Trafficking route for map rendering."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    route_name: str | None = Field(default=None, alias="routeName")
    trafficking_type: str | None = Field(default=None, alias="traffickingType")
    confidence: float | None = None
    geometry: GeoJSONGeometry | None = None
