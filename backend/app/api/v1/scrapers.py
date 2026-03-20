"""Scraper health monitoring API endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.news_articles import DataSource, NewsArticle
from app.schemas.scrapers import ScrapersSummary, ScraperStatus

router = APIRouter()

# ── Human-readable schedule map (mirrors schedule.py) ──────────

SCHEDULE_MAP: dict[str, str] = {
    "rss_monitor": "Every 6 hours",
    "dawn_scraper": "Every 6 hours",
    "tribune_scraper": "Every 6 hours",
    "the_news_scraper": "Every 6 hours",
    "ary_scraper": "Every 6 hours",
    "geo_scraper": "Every 6 hours",
    "js_scraper": "Daily",
    "sahil_checker": "Monthly (1st)",
    "tip_report": "Annually (July)",
    "ctdc_updater": "Quarterly",
    "scp": "Weekly (Sunday)",
    "lhc": "Weekly (Sunday)",
    "shc": "Weekly (Sunday)",
    "phc": "Weekly (Sunday)",
    "bhc": "Weekly (Sunday)",
    "ihc": "Weekly (Sunday)",
    "police_punjab": "Monthly (15th)",
    "police_sindh": "Monthly (15th)",
    "police_kp": "Monthly (15th)",
    "police_balochistan": "Monthly (15th)",
    "stateofchildren": "Monthly (1st)",
    "worldbank_api": "Quarterly",
    "unhcr_api": "Quarterly",
}

# Maximum staleness before each frequency is considered "error" (hours)
_STALENESS_ERROR: dict[str, int] = {
    "Every 6 hours": 48,
    "Daily": 72,
    "Weekly (Sunday)": 14 * 24,       # 14 days
    "Monthly (1st)": 45 * 24,         # 45 days
    "Monthly (15th)": 45 * 24,
    "Quarterly": 120 * 24,            # 120 days
    "Annually (July)": 400 * 24,      # ~13 months
}


def _compute_status(
    is_active: bool,
    last_scraped: datetime | None,
    schedule: str | None,
) -> str:
    """Derive health status from activity flag and last execution time."""
    if not is_active:
        return "inactive"

    if last_scraped is None:
        return "error"

    now = datetime.now(tz=timezone.utc)
    age_hours = (now - last_scraped).total_seconds() / 3600

    error_threshold = _STALENESS_ERROR.get(schedule or "", 48)
    warning_threshold = error_threshold * 0.75

    if age_hours > error_threshold:
        return "error"
    if age_hours > warning_threshold:
        return "warning"
    return "healthy"


@router.get("/", response_model=list[ScraperStatus])
async def list_scrapers(
    db: AsyncSession = Depends(get_db),
) -> list[ScraperStatus]:
    """Return all data sources with computed health status."""
    now_minus_24h = datetime.now(tz=timezone.utc) - timedelta(hours=24)

    # Subquery: articles per source in last 24h
    articles_sub = (
        select(
            NewsArticle.source_name,
            func.count().label("cnt"),
        )
        .where(NewsArticle.created_at > now_minus_24h)
        .group_by(NewsArticle.source_name)
        .subquery()
    )

    stmt = (
        select(DataSource, articles_sub.c.cnt)
        .outerjoin(articles_sub, DataSource.scraper_name == articles_sub.c.source_name)
        .order_by(DataSource.source_type, DataSource.name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        ScraperStatus(
            id=ds.id,
            name=ds.name,
            scraperName=ds.scraper_name,
            sourceType=ds.source_type,
            url=ds.url,
            isActive=ds.is_active,
            lastScraped=ds.last_scraped,
            lastUpdated=ds.last_updated,
            recordCount=ds.record_count or 0,
            articlesLast24h=cnt or 0,
            status=_compute_status(
                ds.is_active,
                ds.last_scraped,
                SCHEDULE_MAP.get(ds.scraper_name or "", None),
            ),
            schedule=SCHEDULE_MAP.get(ds.scraper_name or "", None),
            notes=ds.notes,
        )
        for ds, cnt in rows
    ]


@router.get("/summary", response_model=ScrapersSummary)
async def scrapers_summary(
    db: AsyncSession = Depends(get_db),
) -> ScrapersSummary:
    """Return aggregate KPIs across all scrapers."""
    now_minus_24h = datetime.now(tz=timezone.utc) - timedelta(hours=24)

    # Fetch all data sources
    ds_result = await db.execute(
        select(DataSource).order_by(DataSource.id)
    )
    sources = ds_result.scalars().all()

    # Total articles
    total_articles_result = await db.execute(
        select(func.count()).select_from(NewsArticle)
    )
    total_articles = total_articles_result.scalar() or 0

    # Articles last 24h
    articles_24h_result = await db.execute(
        select(func.count())
        .select_from(NewsArticle)
        .where(NewsArticle.created_at > now_minus_24h)
    )
    articles_last_24h = articles_24h_result.scalar() or 0

    # Compute per-scraper status
    statuses: list[str] = []
    last_activity: datetime | None = None
    for ds in sources:
        schedule = SCHEDULE_MAP.get(ds.scraper_name or "", None)
        statuses.append(_compute_status(ds.is_active, ds.last_scraped, schedule))
        if ds.last_scraped is not None:
            if last_activity is None or ds.last_scraped > last_activity:
                last_activity = ds.last_scraped

    return ScrapersSummary(
        totalScrapers=len(sources),
        activeScrapers=sum(1 for ds in sources if ds.is_active),
        healthyScrapers=statuses.count("healthy"),
        warningScrapers=statuses.count("warning"),
        errorScrapers=statuses.count("error"),
        totalArticles=total_articles,
        articlesLast24h=articles_last_24h,
        lastActivity=last_activity,
    )
