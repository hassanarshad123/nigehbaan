"""Scraper command center API — monitoring, control, and execution history."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.news_articles import DataSource, NewsArticle
from app.models.scraper_runs import ScraperRun
from app.schemas.scrapers import ScrapersSummary, ScraperStatus

router = APIRouter()

# ── Human-readable schedule map (mirrors schedule.py) ──────────

SCHEDULE_MAP: dict[str, str] = {
    # ── News (every 6 hours) ──────────────────────────────────────
    "rss_monitor": "Every 6 hours",
    "dawn": "Every 6 hours",
    "tribune": "Every 6 hours",
    "the_news": "Every 6 hours",
    "ary_news": "Every 6 hours",
    "geo_news": "Every 6 hours",
    "jang_urdu": "Every 6 hours",
    "express_urdu": "Every 6 hours",
    "bbc_urdu": "Every 6 hours",
    "geo_urdu": "Every 6 hours",
    # ── Courts (weekly Sunday) ────────────────────────────────────
    "scp": "Weekly (Sun)",
    "lhc": "Weekly (Sun)",
    "shc": "Weekly (Sun)",
    "phc": "Weekly (Sun)",
    "bhc": "Weekly (Sun)",
    "ihc": "Weekly (Sun)",
    "commonlii": "Weekly (Sun)",
    # ── Police (monthly 15th) ─────────────────────────────────────
    "police_punjab": "Monthly (15th)",
    "police_sindh": "Monthly (15th)",
    "police_kp": "Monthly (15th)",
    "police_balochistan": "Monthly (15th)",
    # ── Monthly ───────────────────────────────────────────────────
    "stateofchildren": "Monthly (1st)",
    "drf_newsletters": "Monthly",
    # ── Quarterly ─────────────────────────────────────────────────
    "ctdc": "Quarterly",
    "worldbank_api": "Quarterly",
    "unhcr_api": "Quarterly",
    "dhs_api": "Quarterly",
    "pahchaan": "Quarterly",
    "unicef_pakistan": "Quarterly",
    "cpwb_punjab": "Quarterly",
    "ilostat_api": "Quarterly",
    "brick_kiln_dashboard": "Quarterly",
    "ctdc_dataset": "Quarterly",
    "unicef_sdmx": "Quarterly",
    "jpp_data": "Quarterly",
    "roshni_helpline": "Quarterly",
    "unodc": "Quarterly",
    "kpcpwc": "Quarterly",
    "ssdo_checker": "Quarterly",
    "mohr_checker": "Quarterly",
    "border_crossings": "Quarterly",
    "flood_extent": "Quarterly",
    # ── Semi-annual ───────────────────────────────────────────────
    "ncmec": "Semi-annual",
    "meta_transparency": "Semi-annual",
    "google_transparency": "Semi-annual",
    # ── Annually ──────────────────────────────────────────────────
    "sahil": "Annually (Jan)",
    "tip_report": "Annually (Jul)",
    "ecpat": "Annually",
    "ncrc": "Annually",
    "dol_child_labor": "Annually (Oct)",
    "dol_annual_report": "Annually (Oct)",
    "dol_tvpra": "Annually (Oct)",
    "girls_not_brides": "Annually",
    "world_prison_brief": "Annually",
    "corporal_punishment": "Annually",
    "zenodo_kilns": "Annually",
    "iwf_reports": "Annually",
    "weprotect_gta": "Annually",
    "bytes_for_all": "Annually",
    "labour_surveys": "Annually",
    "bllf": "Annually",
    "brookings_bride": "Annually",
    "csj_conversion": "Annually",
    "provincial_labour_surveys": "Annually",
    "nchr_organ": "Annually",
    "sparc_reports": "Annually",
    "zenodo_kilns_loader": "Annually",
    "walkfree_gsi": "Annually",
}

# Maximum staleness before each frequency is "error" (hours)
_STALENESS_ERROR: dict[str, int] = {
    "Every 6 hours": 48,
    "Daily": 72,
    "Weekly (Sun)": 14 * 24,
    "Monthly": 45 * 24,
    "Monthly (1st)": 45 * 24,
    "Monthly (15th)": 45 * 24,
    "Quarterly": 120 * 24,
    "Semi-annual": 200 * 24,
    "Annually": 400 * 24,
    "Annually (Jan)": 400 * 24,
    "Annually (Jul)": 400 * 24,
}

# ── Celery task name mapping ───────────────────────────────────
# Values are either a task name string, or a (task_name, args) tuple
# for tasks that require positional arguments (courts, police).

TASK_MAP: dict[str, str | tuple[str, tuple]] = {
    # ── News scrapers ─────────────────────────────────────────────
    "rss_monitor": "app.tasks.scraping_tasks.scrape_news_rss",
    "dawn": "app.tasks.scraping_tasks.scrape_news_dawn",
    "tribune": "app.tasks.scraping_tasks.scrape_news_tribune",
    "the_news": "app.tasks.scraping_tasks.scrape_news_the_news",
    "ary_news": "app.tasks.scraping_tasks.scrape_news_ary",
    "geo_news": "app.tasks.scraping_tasks.scrape_news_geo",
    "jang_urdu": "app.tasks.scraping_tasks.scrape_news_jang_urdu",
    "express_urdu": "app.tasks.scraping_tasks.scrape_news_express_urdu",
    "bbc_urdu": "app.tasks.scraping_tasks.scrape_news_bbc_urdu",
    "geo_urdu": "app.tasks.scraping_tasks.scrape_news_geo_urdu",
    # ── Courts (with court_name arg) ──────────────────────────────
    "scp": ("app.tasks.scraping_tasks.scrape_courts", ("scp",)),
    "lhc": ("app.tasks.scraping_tasks.scrape_courts", ("lhc",)),
    "shc": ("app.tasks.scraping_tasks.scrape_courts", ("shc",)),
    "phc": ("app.tasks.scraping_tasks.scrape_courts", ("phc",)),
    "bhc": ("app.tasks.scraping_tasks.scrape_courts", ("bhc",)),
    "ihc": ("app.tasks.scraping_tasks.scrape_courts", ("ihc",)),
    "commonlii": ("app.tasks.scraping_tasks.scrape_courts", ("commonlii",)),
    # ── Police (with province arg) ────────────────────────────────
    "police_punjab": ("app.tasks.scraping_tasks.scrape_police_data", ("punjab",)),
    "police_sindh": ("app.tasks.scraping_tasks.scrape_police_data", ("sindh",)),
    "police_kp": ("app.tasks.scraping_tasks.scrape_police_data", ("kp",)),
    "police_balochistan": ("app.tasks.scraping_tasks.scrape_police_data", ("balochistan",)),
    # ── Government / NGO ──────────────────────────────────────────
    "sahil": "app.tasks.scraping_tasks.scrape_sahil",
    "stateofchildren": "app.tasks.scraping_tasks.scrape_stateofchildren",
    "pahchaan": "app.tasks.scraping_tasks.scrape_pahchaan",
    "cpwb_punjab": "app.tasks.scraping_tasks.scrape_cpwb_punjab",
    "ncrc": "app.tasks.scraping_tasks.scrape_ncrc",
    "roshni_helpline": "app.tasks.scraping_tasks.scrape_roshni_helpline",
    "bllf": "app.tasks.scraping_tasks.scrape_bllf",
    "drf_newsletters": "app.tasks.scraping_tasks.scrape_drf_newsletters",
    "bytes_for_all": "app.tasks.scraping_tasks.scrape_bytes_for_all",
    "labour_surveys": "app.tasks.scraping_tasks.scrape_labour_surveys",
    "provincial_labour_surveys": "app.tasks.scraping_tasks.scrape_provincial_labour_surveys",
    "nchr_organ": "app.tasks.scraping_tasks.scrape_nchr_organ",
    "sparc_reports": "app.tasks.scraping_tasks.scrape_sparc_reports",
    "csj_conversion": "app.tasks.scraping_tasks.scrape_csj_conversion",
    "brick_kiln_dashboard": "app.tasks.scraping_tasks.scrape_brick_kiln_dashboard",
    "kpcpwc": "app.tasks.scraping_tasks.scrape_kpcpwc",
    "ssdo_checker": "app.tasks.scraping_tasks.scrape_ssdo_checker",
    "mohr_checker": "app.tasks.scraping_tasks.scrape_mohr_checker",
    # ── Data loaders ──────────────────────────────────────────────
    "border_crossings": "app.tasks.scraping_tasks.load_border_crossings",
    "zenodo_kilns_loader": "app.tasks.scraping_tasks.load_zenodo_kilns",
    "walkfree_gsi": "app.tasks.scraping_tasks.load_walkfree_gsi",
    "flood_extent": "app.tasks.scraping_tasks.load_flood_extent",
    # ── International ─────────────────────────────────────────────
    "tip_report": "app.tasks.scraping_tasks.scrape_tip_report",
    "ctdc": "app.tasks.scraping_tasks.update_ctdc",
    "ctdc_dataset": "app.tasks.scraping_tasks.scrape_ctdc_dataset",
    "unodc": "app.tasks.scraping_tasks.scrape_unodc",
    "worldbank_api": "app.tasks.scraping_tasks.scrape_worldbank_api",
    "unhcr_api": "app.tasks.scraping_tasks.scrape_unhcr_api",
    "dhs_api": "app.tasks.scraping_tasks.scrape_dhs_api",
    "ilostat_api": "app.tasks.scraping_tasks.scrape_ilostat_api",
    "unicef_pakistan": "app.tasks.scraping_tasks.scrape_unicef_pakistan",
    "unicef_sdmx": "app.tasks.scraping_tasks.scrape_unicef_sdmx",
    "ecpat": "app.tasks.scraping_tasks.scrape_ecpat",
    "ncmec": "app.tasks.scraping_tasks.scrape_ncmec",
    "iwf_reports": "app.tasks.scraping_tasks.scrape_iwf_reports",
    "meta_transparency": "app.tasks.scraping_tasks.scrape_meta_transparency",
    "google_transparency": "app.tasks.scraping_tasks.scrape_google_transparency",
    "weprotect_gta": "app.tasks.scraping_tasks.scrape_weprotect_gta",
    "girls_not_brides": "app.tasks.scraping_tasks.scrape_girls_not_brides",
    "corporal_punishment": "app.tasks.scraping_tasks.scrape_corporal_punishment",
    "dol_child_labor": "app.tasks.scraping_tasks.scrape_dol_child_labor",
    "dol_annual_report": "app.tasks.scraping_tasks.scrape_dol_annual_report",
    "dol_tvpra": "app.tasks.scraping_tasks.scrape_dol_tvpra",
    "brookings_bride": "app.tasks.scraping_tasks.scrape_brookings_bride",
    "jpp_data": "app.tasks.scraping_tasks.scrape_jpp_data",
    "world_prison_brief": "app.tasks.scraping_tasks.scrape_world_prison_brief",
    "zenodo_kilns": "app.tasks.scraping_tasks.scrape_zenodo_kilns",
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


# ═══════════════════════════════════════════════════════════════
# READ ENDPOINTS
# ═══════════════════════════════════════════════════════════════


@router.get("/", response_model=list[ScraperStatus])
async def list_scrapers(
    db: AsyncSession = Depends(get_db),
) -> list[ScraperStatus]:
    """Return all data sources with computed health status."""
    now_minus_24h = datetime.now(tz=timezone.utc) - timedelta(hours=24)

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
        .outerjoin(
            articles_sub,
            DataSource.scraper_name == articles_sub.c.source_name,
        )
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

    ds_result = await db.execute(select(DataSource).order_by(DataSource.id))
    sources = ds_result.scalars().all()

    total_articles_result = await db.execute(
        select(func.count()).select_from(NewsArticle)
    )
    total_articles = total_articles_result.scalar() or 0

    articles_24h_result = await db.execute(
        select(func.count())
        .select_from(NewsArticle)
        .where(NewsArticle.created_at > now_minus_24h)
    )
    articles_last_24h = articles_24h_result.scalar() or 0

    statuses: list[str] = []
    last_activity: datetime | None = None
    for ds in sources:
        schedule = SCHEDULE_MAP.get(ds.scraper_name or "", None)
        statuses.append(
            _compute_status(ds.is_active, ds.last_scraped, schedule)
        )
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


# ═══════════════════════════════════════════════════════════════
# ACTIVITY & LOGS
# ═══════════════════════════════════════════════════════════════


class ActivityItem(BaseModel):
    model_config = {"frozen": True, "populate_by_name": True}
    id: int
    scraper_name: str = Field(alias="scraperName")
    status: str
    started_at: datetime | None = Field(alias="startedAt")
    completed_at: datetime | None = Field(alias="completedAt")
    records_found: int = Field(default=0, alias="recordsFound")
    records_saved: int = Field(default=0, alias="recordsSaved")
    error_message: str | None = Field(default=None, alias="errorMessage")
    duration_seconds: float | None = Field(default=None, alias="durationSeconds")
    triggered_by: str | None = Field(default=None, alias="triggeredBy")


@router.get("/activity", response_model=list[ActivityItem])
async def scraper_activity(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[ActivityItem]:
    """Recent scraper execution activity (newest first)."""
    try:
        result = await db.execute(
            select(ScraperRun)
            .order_by(desc(ScraperRun.started_at))
            .limit(limit)
        )
        runs = result.scalars().all()
        return [
            ActivityItem(
                id=r.id,
                scraperName=r.scraper_name,
                status=r.status,
                startedAt=r.started_at,
                completedAt=r.completed_at,
                recordsFound=r.records_found or 0,
                recordsSaved=r.records_saved or 0,
                errorMessage=r.error_message,
                durationSeconds=r.duration_seconds,
                triggeredBy=r.triggered_by,
            )
            for r in runs
        ]
    except Exception:
        # Table may not exist yet
        return []


@router.get("/{name}/logs", response_model=list[ActivityItem])
async def scraper_logs(
    name: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[ActivityItem]:
    """Execution history for a specific scraper."""
    try:
        result = await db.execute(
            select(ScraperRun)
            .where(ScraperRun.scraper_name == name)
            .order_by(desc(ScraperRun.started_at))
            .limit(limit)
        )
        runs = result.scalars().all()
        return [
            ActivityItem(
                id=r.id,
                scraperName=r.scraper_name,
                status=r.status,
                startedAt=r.started_at,
                completedAt=r.completed_at,
                recordsFound=r.records_found or 0,
                recordsSaved=r.records_saved or 0,
                errorMessage=r.error_message,
                durationSeconds=r.duration_seconds,
                triggeredBy=r.triggered_by,
            )
            for r in runs
        ]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# QUEUE STATUS
# ═══════════════════════════════════════════════════════════════


class QueueStats(BaseModel):
    model_config = {"frozen": True, "populate_by_name": True}
    active_tasks: int = Field(default=0, alias="activeTasks")
    reserved_tasks: int = Field(default=0, alias="reservedTasks")
    scheduled_tasks: int = Field(default=0, alias="scheduledTasks")
    active_details: list[dict[str, Any]] = Field(
        default_factory=list, alias="activeDetails"
    )


@router.get("/queue", response_model=QueueStats)
async def queue_status() -> QueueStats:
    """Current Celery queue statistics."""
    try:
        from app.tasks.celery_app import celery_app

        inspector = celery_app.control.inspect(timeout=3)
        active = inspector.active() or {}
        reserved = inspector.reserved() or {}
        scheduled = inspector.scheduled() or {}

        active_count = sum(len(tasks) for tasks in active.values())
        reserved_count = sum(len(tasks) for tasks in reserved.values())
        scheduled_count = sum(len(tasks) for tasks in scheduled.values())

        active_details = []
        for _worker, tasks in active.items():
            for task in tasks:
                active_details.append(
                    {
                        "id": task.get("id", ""),
                        "name": task.get("name", ""),
                        "startedAt": task.get("time_start"),
                    }
                )

        return QueueStats(
            activeTasks=active_count,
            reservedTasks=reserved_count,
            scheduledTasks=scheduled_count,
            activeDetails=active_details,
        )
    except Exception:
        return QueueStats()


# ═══════════════════════════════════════════════════════════════
# CONTROL ENDPOINTS
# ═══════════════════════════════════════════════════════════════


class TriggerResponse(BaseModel):
    model_config = {"frozen": True, "populate_by_name": True}
    success: bool
    task_id: str | None = Field(default=None, alias="taskId")
    scraper_name: str = Field(alias="scraperName")
    message: str


@router.post("/{name}/trigger", response_model=TriggerResponse)
async def trigger_scraper(
    name: str,
    db: AsyncSession = Depends(get_db),
) -> TriggerResponse:
    """Manually trigger a scraper task."""
    from app.tasks.celery_app import celery_app

    entry = TASK_MAP.get(name)
    task_args: tuple = ()
    if isinstance(entry, tuple):
        task_name, task_args = entry
    elif isinstance(entry, str):
        task_name = entry
    else:
        # Fallback: try a generic pattern
        task_name = f"app.tasks.scraping_tasks.scrape_{name}"

    try:
        result = celery_app.send_task(task_name, args=task_args)

        # Log the run
        run = ScraperRun(
            scraper_name=name,
            task_id=result.id,
            status="pending",
            triggered_by="manual",
        )
        db.add(run)
        await db.commit()

        return TriggerResponse(
            success=True,
            taskId=result.id,
            scraperName=name,
            message=f"Task {task_name} dispatched",
        )
    except Exception as exc:
        return TriggerResponse(
            success=False,
            scraperName=name,
            message=f"Failed to trigger: {exc}",
        )


@router.post("/trigger-all", response_model=list[TriggerResponse])
async def trigger_all_scrapers(
    db: AsyncSession = Depends(get_db),
) -> list[TriggerResponse]:
    """Trigger all mapped scrapers."""
    from app.tasks.celery_app import celery_app

    results = []
    for name, entry in TASK_MAP.items():
        try:
            if isinstance(entry, tuple):
                task_name, task_args = entry
                result = celery_app.send_task(task_name, args=task_args)
            else:
                task_name = entry
                result = celery_app.send_task(task_name)
            run = ScraperRun(
                scraper_name=name,
                task_id=result.id,
                status="pending",
                triggered_by="manual",
            )
            db.add(run)
            results.append(
                TriggerResponse(
                    success=True,
                    taskId=result.id,
                    scraperName=name,
                    message=f"Dispatched {task_name}",
                )
            )
        except Exception as exc:
            results.append(
                TriggerResponse(
                    success=False,
                    scraperName=name,
                    message=str(exc),
                )
            )
    await db.commit()
    return results


@router.post("/{name}/stop", response_model=TriggerResponse)
async def stop_scraper(
    name: str,
    task_id: str | None = None,
) -> TriggerResponse:
    """Stop/revoke a running scraper task."""
    from app.tasks.celery_app import celery_app

    if not task_id:
        # Find the most recent running task for this scraper
        return TriggerResponse(
            success=False,
            scraperName=name,
            message="task_id required to stop a task",
        )

    try:
        celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
        return TriggerResponse(
            success=True,
            taskId=task_id,
            scraperName=name,
            message=f"Task {task_id} revoked",
        )
    except Exception as exc:
        return TriggerResponse(
            success=False,
            scraperName=name,
            message=f"Failed to stop: {exc}",
        )


@router.post("/{name}/toggle", response_model=TriggerResponse)
async def toggle_scraper(
    name: str,
    db: AsyncSession = Depends(get_db),
) -> TriggerResponse:
    """Toggle a scraper's active status (enable/disable)."""
    result = await db.execute(
        select(DataSource).where(
            (DataSource.scraper_name == name) | (DataSource.name == name)
        )
    )
    ds = result.scalar_one_or_none()

    if not ds:
        raise HTTPException(status_code=404, detail=f"Scraper '{name}' not found")

    new_state = not ds.is_active
    ds.is_active = new_state
    await db.commit()

    return TriggerResponse(
        success=True,
        scraperName=name,
        message=f"Scraper {'enabled' if new_state else 'disabled'}",
    )
