"""Celery tasks for data scraping and ingestion.

Each task instantiates the appropriate scraper, runs it, saves raw data,
persists articles to the database, and enqueues AI processing per article.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _save_news_articles(records: list[dict[str, Any]], source_name: str) -> list[int]:
    """Upsert scraped articles into news_articles and return their IDs."""
    from app.database import async_session_factory
    from app.models.news_articles import NewsArticle

    article_ids: list[int] = []

    async with async_session_factory() as session:
        for record in records:
            url = record.get("url", "")
            if not url:
                continue

            # Check if article already exists
            result = await session.execute(
                select(NewsArticle.id).where(NewsArticle.url == url)
            )
            existing_id = result.scalar_one_or_none()

            if existing_id is not None:
                article_ids.append(existing_id)
                continue

            published_date = None
            raw_date = record.get("published_date", "")
            if raw_date:
                try:
                    if isinstance(raw_date, str):
                        # Handle ISO format and common date strings
                        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                            try:
                                published_date = datetime.strptime(
                                    raw_date[:26], fmt
                                ).date()
                                break
                            except ValueError:
                                continue
                    elif hasattr(raw_date, "date"):
                        published_date = raw_date.date()
                except Exception:
                    pass

            article = NewsArticle(
                source_name=source_name,
                url=url,
                title=record.get("title", "")[:2000] if record.get("title") else None,
                published_date=published_date,
                full_text=record.get("full_text") or record.get("summary", ""),
            )
            session.add(article)
            await session.flush()
            article_ids.append(article.id)

        await session.commit()

    return article_ids


async def _update_data_source(
    scraper_name: str,
    record_count: int,
    status: str = "success",
    error: str | None = None,
) -> None:
    """Update the data_sources table with scraping results."""
    from app.database import async_session_factory
    from app.models.news_articles import DataSource

    async with async_session_factory() as session:
        result = await session.execute(
            select(DataSource).where(DataSource.scraper_name == scraper_name)
        )
        ds = result.scalar_one_or_none()

        if ds is not None:
            ds.last_scraped = datetime.now(timezone.utc)
            ds.record_count = (ds.record_count or 0) + record_count
        else:
            ds = DataSource(
                name=scraper_name,
                scraper_name=scraper_name,
                last_scraped=datetime.now(timezone.utc),
                record_count=record_count,
                is_active=True,
            )
            session.add(ds)

        await session.commit()


async def _run_scraper(module_path: str, class_name: str) -> list[dict[str, Any]]:
    """Dynamically import and run a scraper class."""
    mod = __import__(module_path, fromlist=[class_name])
    cls = getattr(mod, class_name)
    scraper = cls()
    return await scraper.run()


def _enqueue_ai_processing(article_ids: list[int]) -> None:
    """Enqueue AI processing tasks for each article."""
    from app.tasks.processing_tasks import process_article_ai

    for article_id in article_ids:
        process_article_ai.delay(article_id)


# ---------------------------------------------------------------------------
# News scrapers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_rss",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def scrape_news_rss(self) -> dict:
    """Scrape Pakistani news RSS feeds via the RSSMonitor aggregator."""
    logger.info("Starting RSS news scrape")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.news.rss_monitor", "RSSMonitor"
        )
        if records:
            article_ids = await _save_news_articles(records, "rss_monitor")
            await _update_data_source("rss_monitor", len(records))
            _enqueue_ai_processing(article_ids)
            return {"status": "completed", "articles_found": len(records), "saved": len(article_ids)}
        await _update_data_source("rss_monitor", 0)
        return {"status": "completed", "articles_found": 0}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_dawn",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def scrape_news_dawn(self) -> dict:
    """Scrape Dawn newspaper for child protection articles."""
    logger.info("Starting Dawn scrape")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.news.dawn_scraper", "DawnScraper"
        )
        if records:
            article_ids = await _save_news_articles(records, "dawn")
            await _update_data_source("dawn", len(records))
            _enqueue_ai_processing(article_ids)
            return {"status": "completed", "articles_found": len(records), "saved": len(article_ids)}
        await _update_data_source("dawn", 0)
        return {"status": "completed", "articles_found": 0}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_tribune",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def scrape_news_tribune(self) -> dict:
    """Scrape Express Tribune for child protection articles."""
    logger.info("Starting Tribune scrape")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.news.tribune_scraper", "TribuneScraper"
        )
        if records:
            article_ids = await _save_news_articles(records, "tribune")
            await _update_data_source("tribune", len(records))
            _enqueue_ai_processing(article_ids)
            return {"status": "completed", "articles_found": len(records), "saved": len(article_ids)}
        await _update_data_source("tribune", 0)
        return {"status": "completed", "articles_found": 0}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_the_news",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def scrape_news_the_news(self) -> dict:
    """Scrape The News International for child protection articles."""
    logger.info("Starting The News scrape")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.news.the_news_scraper", "TheNewsScraper"
        )
        if records:
            article_ids = await _save_news_articles(records, "the_news")
            await _update_data_source("the_news", len(records))
            _enqueue_ai_processing(article_ids)
            return {"status": "completed", "articles_found": len(records), "saved": len(article_ids)}
        await _update_data_source("the_news", 0)
        return {"status": "completed", "articles_found": 0}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_ary",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def scrape_news_ary(self) -> dict:
    """Scrape ARY News for child protection articles."""
    logger.info("Starting ARY News scrape")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.news.ary_scraper", "ARYScraper"
        )
        if records:
            article_ids = await _save_news_articles(records, "ary_news")
            await _update_data_source("ary_news", len(records))
            _enqueue_ai_processing(article_ids)
            return {"status": "completed", "articles_found": len(records), "saved": len(article_ids)}
        await _update_data_source("ary_news", 0)
        return {"status": "completed", "articles_found": 0}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_geo",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def scrape_news_geo(self) -> dict:
    """Scrape Geo News for child protection articles."""
    logger.info("Starting Geo News scrape")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.news.geo_scraper", "GeoScraper"
        )
        if records:
            article_ids = await _save_news_articles(records, "geo_news")
            await _update_data_source("geo_news", len(records))
            _enqueue_ai_processing(article_ids)
            return {"status": "completed", "articles_found": len(records), "saved": len(article_ids)}
        await _update_data_source("geo_news", 0)
        return {"status": "completed", "articles_found": 0}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_js",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def scrape_news_js(self) -> dict:
    """Scrape JS-rendered news sites that require browser automation.

    Runs individual news scrapers that might need Playwright for JS-heavy sites.
    """
    logger.info("Starting JS news scrape")
    results = {}

    # Run each JS-capable scraper
    scrapers = [
        ("data.scrapers.news.ary_scraper", "ARYScraper", "ary_news"),
        ("data.scrapers.news.geo_scraper", "GeoScraper", "geo_news"),
    ]

    async def _run():
        total = 0
        for module_path, class_name, source_name in scrapers:
            try:
                records = await _run_scraper(module_path, class_name)
                if records:
                    article_ids = await _save_news_articles(records, source_name)
                    await _update_data_source(source_name, len(records))
                    _enqueue_ai_processing(article_ids)
                    total += len(records)
            except Exception as exc:
                logger.error("JS scraper %s failed: %s", class_name, exc)
        return {"status": "completed", "articles_found": total}

    return _run_async(_run())


# ---------------------------------------------------------------------------
# Report & NGO scrapers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.scraping_tasks.check_sahil_updates",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=120,
)
def check_sahil_updates(self) -> dict:
    """Check Sahil (NGO) website for new annual reports and data updates."""
    logger.info("Checking Sahil for updates")

    async def _run():
        try:
            records = await _run_scraper(
                "data.scrapers.government.mohr_checker", "MoHRChecker"
            )
            await _update_data_source("sahil", len(records))
            return {"status": "completed", "new_reports": len(records)}
        except Exception as exc:
            logger.error("Sahil checker failed: %s", exc)
            await _update_data_source("sahil", 0, error=str(exc))
            return {"status": "error", "error": str(exc)}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_tip_report",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=120,
)
def scrape_tip_report(self) -> dict:
    """Download and parse the latest US TIP Report for Pakistan."""
    logger.info("Scraping TIP report")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.international.tip_report", "TIPReportScraper"
        )
        await _update_data_source("tip_report", len(records))
        return {"status": "completed", "records": len(records)}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.update_ctdc",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=120,
)
def update_ctdc(self) -> dict:
    """Pull latest data from the Counter-Trafficking Data Collaborative API."""
    logger.info("Updating CTDC data")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.international.unodc", "UNODCScraper"
        )
        await _update_data_source("ctdc", len(records))
        return {"status": "completed", "records_updated": len(records)}

    return _run_async(_run())


# ---------------------------------------------------------------------------
# Court scrapers
# ---------------------------------------------------------------------------

COURT_SCRAPERS: dict[str, tuple[str, str]] = {
    "scp": ("data.scrapers.courts.scp", "SCPScraper"),
    "lhc": ("data.scrapers.courts.lhc", "LHCScraper"),
    "shc": ("data.scrapers.courts.shc", "SHCScraper"),
    "phc": ("data.scrapers.courts.phc", "PHCScraper"),
    "bhc": ("data.scrapers.courts.bhc", "BHCScraper"),
    "ihc": ("data.scrapers.courts.ihc", "IHCScraper"),
}


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_courts",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=120,
)
def scrape_courts(self, court_name: str) -> dict:
    """Scrape court judgments from the specified high court or supreme court.

    Args:
        court_name: One of scp, lhc, shc, phc, bhc, ihc.
    """
    logger.info("Scraping court: %s", court_name)

    if court_name not in COURT_SCRAPERS:
        return {"status": "error", "error": f"Unknown court: {court_name}"}

    module_path, class_name = COURT_SCRAPERS[court_name]

    async def _run():
        records = await _run_scraper(module_path, class_name)
        await _update_data_source(f"court_{court_name}", len(records))
        return {
            "status": "completed",
            "court": court_name,
            "judgments_found": len(records),
        }

    return _run_async(_run())


# ---------------------------------------------------------------------------
# Police scrapers
# ---------------------------------------------------------------------------

POLICE_SCRAPERS: dict[str, tuple[str, str]] = {
    "punjab": ("data.scrapers.government.punjab_police", "PunjabPoliceScraper"),
    "sindh": ("data.scrapers.government.sindh_police", "SindhPoliceScraper"),
}


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_police_data",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=120,
)
def scrape_police_data(self, province: str) -> dict:
    """Scrape provincial police crime data portals.

    Args:
        province: One of punjab, sindh, kp, balochistan.
    """
    logger.info("Scraping police data for province: %s", province)

    if province not in POLICE_SCRAPERS:
        logger.warning("No scraper for province %s yet", province)
        return {"status": "skipped", "province": province, "reason": "no scraper available"}

    module_path, class_name = POLICE_SCRAPERS[province]

    async def _run():
        records = await _run_scraper(module_path, class_name)
        await _update_data_source(f"police_{province}", len(records))
        return {
            "status": "completed",
            "province": province,
            "records_found": len(records),
        }

    return _run_async(_run())


# ---------------------------------------------------------------------------
# Other government & international scrapers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_stateofchildren",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=120,
)
def scrape_stateofchildren(self) -> dict:
    """Scrape State of Children reports for updated statistics."""
    logger.info("Scraping State of Children data")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.government.stateofchildren", "StateOfChildrenScraper"
        )
        await _update_data_source("stateofchildren", len(records))
        return {"status": "completed", "indicators_updated": len(records)}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_worldbank_api",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=120,
)
def scrape_worldbank_api(self) -> dict:
    """Pull Pakistan indicators from the World Bank Open Data API."""
    logger.info("Querying World Bank API")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.international.worldbank_api", "WorldBankAPIScraper"
        )
        await _update_data_source("worldbank_api", len(records))
        return {"status": "completed", "indicators_updated": len(records)}

    return _run_async(_run())


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_unhcr_api",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=120,
)
def scrape_unhcr_api(self) -> dict:
    """Pull refugee population data from the UNHCR API."""
    logger.info("Querying UNHCR API")

    async def _run():
        records = await _run_scraper(
            "data.scrapers.international.unhcr_api", "UNHCRAPIScraper"
        )
        await _update_data_source("unhcr_api", len(records))
        return {"status": "completed", "records_updated": len(records)}

    return _run_async(_run())
