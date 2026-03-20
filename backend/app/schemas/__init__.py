"""Re-export all Pydantic schemas for convenient imports."""

from app.schemas.common import (
    APIResponse,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    GeoJSONProperties,
    PaginationParams,
)
from app.schemas.map import (
    BorderCrossingPoint,
    BoundaryResponse,
    IncidentMapPoint,
    KilnMapPoint,
    RouteResponse,
)
from app.schemas.dashboard import (
    CaseTypeBreakdownItem,
    ConvictionRatePoint,
    DashboardSummary,
    ProvinceComparisonItem,
    TrendDataPoint,
)
from app.schemas.reports import ReportCreate, ReportResponse, ReportStatus
from app.schemas.districts import DistrictListItem, DistrictProfile, DistrictVulnerability
from app.schemas.legal import ConvictionRateResponse, JudgmentResponse, JudgmentSearchParams
from app.schemas.search import SearchResult
from app.schemas.export import ExportParams

__all__ = [
    "APIResponse",
    "BorderCrossingPoint",
    "BoundaryResponse",
    "CaseTypeBreakdownItem",
    "ConvictionRatePoint",
    "ConvictionRateResponse",
    "DashboardSummary",
    "DistrictListItem",
    "DistrictProfile",
    "DistrictVulnerability",
    "ExportParams",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "GeoJSONGeometry",
    "GeoJSONProperties",
    "IncidentMapPoint",
    "JudgmentResponse",
    "JudgmentSearchParams",
    "KilnMapPoint",
    "PaginationParams",
    "ProvinceComparisonItem",
    "ReportCreate",
    "ReportResponse",
    "ReportStatus",
    "RouteResponse",
    "SearchResult",
    "TrendDataPoint",
]
