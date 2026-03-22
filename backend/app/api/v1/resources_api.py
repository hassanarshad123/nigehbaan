"""Resources API endpoints for helplines, legal aid, shelters, NGOs."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.resources import Resource

router = APIRouter()


class ResourceItem(BaseModel):
    """A single resource entry."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    category: str
    name: str
    description: str | None = None
    contact: str | None = None
    url: str | None = None
    sort_order: int = Field(default=0, alias="sortOrder")


@router.get("/", response_model=list[ResourceItem])
async def list_resources(
    category: str | None = Query(default=None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
) -> list[ResourceItem]:
    """List active resources, optionally filtered by category."""
    stmt = (
        select(Resource)
        .where(Resource.is_active == True)  # noqa: E712
        .order_by(Resource.category, Resource.sort_order, Resource.name)
    )

    if category is not None:
        stmt = stmt.where(Resource.category == category)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        ResourceItem(
            id=r.id,
            category=r.category,
            name=r.name,
            description=r.description,
            contact=r.contact,
            url=r.url,
            sortOrder=r.sort_order,
        )
        for r in rows
    ]
