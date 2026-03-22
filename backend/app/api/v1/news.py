"""News article API endpoints."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.news_articles import NewsArticle
from app.schemas.news import NewsArticleDetail, NewsArticleListItem

router = APIRouter()

_SNIPPET_MAX_LEN = 200


def _make_snippet(full_text: str | None) -> str | None:
    """Truncate full_text to a short snippet."""
    if not full_text:
        return None
    text = full_text.strip()
    if len(text) <= _SNIPPET_MAX_LEN:
        return text
    return text[:_SNIPPET_MAX_LEN].rsplit(" ", 1)[0] + "..."


@router.get("/sources", response_model=list[str])
async def list_sources(
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """Return distinct news source names from the database."""
    result = await db.execute(
        select(distinct(NewsArticle.source_name))
        .where(NewsArticle.source_name.isnot(None))
        .order_by(NewsArticle.source_name)
    )
    return [row[0] for row in result.all()]


@router.get("/", response_model=list[NewsArticleListItem])
async def list_news(
    source_name: str | None = Query(default=None, description="Filter by source"),
    date_from: date | None = Query(default=None, description="Start date (inclusive)"),
    date_to: date | None = Query(default=None, description="End date (inclusive)"),
    is_trafficking_relevant: bool | None = Query(default=None, description="Filter by relevance"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[NewsArticleListItem]:
    """List news articles with optional filters and pagination."""
    stmt = select(NewsArticle).order_by(NewsArticle.published_date.desc().nullslast())

    if source_name is not None:
        stmt = stmt.where(NewsArticle.source_name == source_name)
    if date_from is not None:
        stmt = stmt.where(NewsArticle.published_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(NewsArticle.published_date <= date_to)
    if is_trafficking_relevant is not None:
        stmt = stmt.where(NewsArticle.is_trafficking_relevant == is_trafficking_relevant)

    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    articles = result.scalars().all()

    return [
        NewsArticleListItem(
            id=a.id,
            title=a.title,
            sourceName=a.source_name,
            publishedDate=a.published_date,
            snippet=_make_snippet(a.full_text),
            isTraffickingRelevant=a.is_trafficking_relevant,
            extractedLocations=a.extracted_locations,
        )
        for a in articles
    ]


@router.get("/{article_id}", response_model=NewsArticleDetail)
async def get_news_detail(
    article_id: int = Path(..., ge=1, description="News article ID"),
    db: AsyncSession = Depends(get_db),
) -> NewsArticleDetail:
    """Get full detail of a single news article."""
    result = await db.execute(
        select(NewsArticle).where(NewsArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")

    return NewsArticleDetail(
        id=article.id,
        title=article.title,
        sourceName=article.source_name,
        url=article.url,
        publishedDate=article.published_date,
        fullText=article.full_text,
        isTraffickingRelevant=article.is_trafficking_relevant,
        relevanceScore=article.relevance_score,
        extractedIncidents=article.extracted_incidents,
        extractedLocations=article.extracted_locations,
        extractedEntities=article.extracted_entities,
        createdAt=article.created_at or datetime.now(tz=timezone.utc),
    )
