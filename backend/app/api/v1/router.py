"""Aggregate all v1 sub-routers into a single APIRouter."""

from fastapi import APIRouter

from app.api.v1 import dashboard, districts, export, legal, map, reports, scrapers, search

v1_router = APIRouter()

v1_router.include_router(map.router, prefix="/map", tags=["Map Layers"])
v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
v1_router.include_router(districts.router, prefix="/districts", tags=["Districts"])
v1_router.include_router(reports.router, prefix="/reports", tags=["Public Reports"])
v1_router.include_router(legal.router, prefix="/legal", tags=["Legal / Courts"])
v1_router.include_router(search.router, prefix="/search", tags=["Search"])
v1_router.include_router(export.router, prefix="/export", tags=["Export"])
v1_router.include_router(scrapers.router, prefix="/scrapers", tags=["Scrapers"])
