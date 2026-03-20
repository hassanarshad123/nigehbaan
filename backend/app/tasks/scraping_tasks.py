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


async def _save_statistical_reports(records: list[dict[str, Any]], source_name: str) -> int:
    """Upsert scraped records into statistical_reports and return count saved."""
    from app.database import async_session_factory
    from app.models.statistical_reports import StatisticalReport

    saved = 0
    async with async_session_factory() as session:
        for record in records:
            try:
                stmt = pg_insert(StatisticalReport).values(
                    source_name=source_name,
                    report_year=record.get("report_year"),
                    report_title=record.get("report_title"),
                    indicator=record.get("indicator"),
                    value=record.get("value"),
                    unit=record.get("unit"),
                    geographic_scope=record.get("geographic_scope"),
                    district_pcode=record.get("district_pcode"),
                    victim_gender=record.get("victim_gender"),
                    victim_age_bracket=record.get("victim_age_bracket"),
                    pdf_url=record.get("pdf_url"),
                    local_pdf_path=record.get("local_pdf_path"),
                    extraction_method=record.get("extraction_method"),
                    extraction_confidence=record.get("extraction_confidence"),
                    raw_table_data=record.get("raw_table_data"),
                ).on_conflict_do_update(
                    constraint="uq_stat_report_source_year_indicator_geo",
                    set_={
                        "value": record.get("value"),
                        "unit": record.get("unit"),
                        "pdf_url": record.get("pdf_url"),
                        "extraction_method": record.get("extraction_method"),
                        "extraction_confidence": record.get("extraction_confidence"),
                        "raw_table_data": record.get("raw_table_data"),
                    },
                )
                await session.execute(stmt)
                saved += 1
            except Exception as exc:
                logger.warning("Failed to save statistical report: %s", exc)

        await session.commit()

    return saved


async def _save_transparency_reports(records: list[dict[str, Any]], source_name: str) -> int:
    """Upsert scraped records into transparency_reports and return count saved."""
    from app.database import async_session_factory
    from app.models.transparency_reports import TransparencyReport

    saved = 0
    async with async_session_factory() as session:
        for record in records:
            try:
                stmt = pg_insert(TransparencyReport).values(
                    platform=record.get("platform", source_name),
                    report_period=record.get("report_period"),
                    country=record.get("country", "Pakistan"),
                    metric=record.get("metric"),
                    value=record.get("value"),
                    unit=record.get("unit"),
                    source_url=record.get("source_url"),
                ).on_conflict_do_update(
                    constraint="uq_transparency_platform_period_country_metric",
                    set_={
                        "value": record.get("value"),
                        "unit": record.get("unit"),
                        "source_url": record.get("source_url"),
                    },
                )
                await session.execute(stmt)
                saved += 1
            except Exception as exc:
                logger.warning("Failed to save transparency report: %s", exc)

        await session.commit()

    return saved


async def _save_tip_reports(records: list[dict[str, Any]]) -> int:
    """Upsert scraped TIP report records into tip_report_annual and return count saved."""
    from app.database import async_session_factory
    from app.models.tip_report import TipReportAnnual

    saved = 0
    async with async_session_factory() as session:
        for record in records:
            year = record.get("year")
            if not year:
                continue
            try:
                stmt = pg_insert(TipReportAnnual).values(
                    year=year,
                    tier_ranking=record.get("tier_ranking"),
                    ptpa_investigations=record.get("ptpa_investigations"),
                    ptpa_prosecutions=record.get("ptpa_prosecutions"),
                    ptpa_convictions=record.get("ptpa_convictions"),
                    ptpa_sex_trafficking_inv=record.get("ptpa_sex_trafficking_inv"),
                    ptpa_forced_labor_inv=record.get("ptpa_forced_labor_inv"),
                    ppc_investigations=record.get("ppc_investigations"),
                    ppc_prosecutions=record.get("ppc_prosecutions"),
                    ppc_convictions=record.get("ppc_convictions"),
                    victims_identified=record.get("victims_identified"),
                    victims_referred=record.get("victims_referred"),
                    budget_allocated_pkr=record.get("budget_allocated_pkr"),
                    key_findings=record.get("key_findings"),
                    recommendations=record.get("recommendations"),
                    named_hotspots=record.get("named_hotspots"),
                    source_url=record.get("source_url"),
                ).on_conflict_do_update(
                    index_elements=["year"],
                    set_={
                        "tier_ranking": record.get("tier_ranking"),
                        "ptpa_investigations": record.get("ptpa_investigations"),
                        "ptpa_prosecutions": record.get("ptpa_prosecutions"),
                        "ptpa_convictions": record.get("ptpa_convictions"),
                        "victims_identified": record.get("victims_identified"),
                        "victims_referred": record.get("victims_referred"),
                        "key_findings": record.get("key_findings"),
                        "recommendations": record.get("recommendations"),
                        "source_url": record.get("source_url"),
                    },
                )
                await session.execute(stmt)
                saved += 1
            except Exception as exc:
                logger.warning("Failed to save TIP report record: %s", exc)

        await session.commit()

    return saved


async def _save_court_judgments(records: list[dict[str, Any]], source_name: str) -> int:
    """Upsert scraped court judgments using source_url as dedup key."""
    from app.database import async_session_factory
    from app.models.court_judgments import CourtJudgment

    saved = 0
    async with async_session_factory() as session:
        for record in records:
            source_url = record.get("source_url")
            if not source_url:
                continue
            try:
                stmt = pg_insert(CourtJudgment).values(
                    court_name=record.get("court_name"),
                    court_bench=record.get("court_bench"),
                    case_number=record.get("case_number"),
                    judgment_date=record.get("judgment_date"),
                    judge_names=record.get("judge_names"),
                    appellant=record.get("appellant"),
                    respondent=record.get("respondent"),
                    ppc_sections=record.get("ppc_sections"),
                    statutes=record.get("statutes"),
                    is_trafficking_related=record.get("is_trafficking_related"),
                    trafficking_type=record.get("trafficking_type"),
                    incident_district_pcode=record.get("incident_district_pcode"),
                    court_district_pcode=record.get("court_district_pcode"),
                    verdict=record.get("verdict"),
                    sentence=record.get("sentence"),
                    sentence_years=record.get("sentence_years"),
                    judgment_text=record.get("judgment_text"),
                    pdf_url=record.get("pdf_url"),
                    source_url=source_url,
                    nlp_confidence=record.get("nlp_confidence"),
                ).on_conflict_do_nothing(
                    constraint="uq_court_judgment_source_url",
                )
                result = await session.execute(stmt)
                if result.rowcount > 0:
                    saved += 1
            except Exception as exc:
                logger.warning("Failed to save court judgment: %s", exc)

        await session.commit()

    return saved


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
            return {
                "status": "completed",
                "articles_found": len(records),
                "saved": len(article_ids),
            }
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
            return {
                "status": "completed",
                "articles_found": len(records),
                "saved": len(article_ids),
            }
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
            return {
                "status": "completed",
                "articles_found": len(records),
                "saved": len(article_ids),
            }
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
            return {
                "status": "completed",
                "articles_found": len(records),
                "saved": len(article_ids),
            }
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
            return {
                "status": "completed",
                "articles_found": len(records),
                "saved": len(article_ids),
            }
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
            return {
                "status": "completed",
                "articles_found": len(records),
                "saved": len(article_ids),
            }
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
    _results: dict = {}

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
        saved = 0
        if records:
            saved = await _save_tip_reports(records)
        await _update_data_source("tip_report", saved)
        return {"status": "completed", "records": len(records), "saved": saved}

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
        saved = 0
        if records:
            saved = await _save_court_judgments(records, f"court_{court_name}")
        await _update_data_source(f"court_{court_name}", saved)
        return {
            "status": "completed",
            "court": court_name,
            "judgments_found": len(records),
            "saved": saved,
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
        saved = 0
        if records:
            transformed = [
                {
                    "report_year": r.get("report_year") or r.get("year"),
                    "indicator": r.get("crime_category") or r.get("indicator"),
                    "value": r.get("count") or r.get("value"),
                    "unit": r.get("unit", "cases"),
                    "geographic_scope": r.get("geographic_scope", province.title()),
                    "district_pcode": r.get("district_pcode"),
                    "extraction_method": "scraper",
                }
                for r in records
            ]
            saved = await _save_statistical_reports(transformed, f"police_{province}")
        await _update_data_source(f"police_{province}", saved)
        return {
            "status": "completed",
            "province": province,
            "records_found": len(records),
            "saved": saved,
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
        saved = 0
        if records:
            transformed = [
                {
                    "report_year": r.get("report_year") or r.get("year"),
                    "indicator": r.get("indicator"),
                    "value": r.get("value"),
                    "unit": r.get("unit"),
                    "geographic_scope": r.get("geographic_scope", "Pakistan"),
                    "extraction_method": r.get("extraction_method", "scraper"),
                }
                for r in records
            ]
            saved = await _save_statistical_reports(transformed, "stateofchildren")
        await _update_data_source("stateofchildren", saved)
        return {"status": "completed", "indicators_updated": len(records), "saved": saved}

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
        saved = 0
        if records:
            transformed = [
                {
                    "report_year": r.get("report_year") or r.get("year"),
                    "indicator": r.get("indicator"),
                    "value": r.get("value"),
                    "unit": r.get("unit"),
                    "geographic_scope": r.get("geographic_scope", "Pakistan"),
                    "extraction_method": "api",
                }
                for r in records
            ]
            saved = await _save_statistical_reports(transformed, "worldbank_api")
        await _update_data_source("worldbank_api", saved)
        return {"status": "completed", "indicators_updated": len(records), "saved": saved}

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
        saved = 0
        if records:
            transformed = [
                {
                    "report_year": r.get("report_year") or r.get("year"),
                    "indicator": r.get("population_type") or r.get("indicator"),
                    "value": r.get("count") or r.get("value"),
                    "unit": r.get("unit", "persons"),
                    "geographic_scope": r.get("geographic_scope", "Pakistan"),
                    "extraction_method": "api",
                }
                for r in records
            ]
            saved = await _save_statistical_reports(transformed, "unhcr_api")
        await _update_data_source("unhcr_api", saved)
        return {"status": "completed", "records_updated": len(records), "saved": saved}

    return _run_async(_run())


# ---------------------------------------------------------------------------
# Helper: generic statistical report task
# ---------------------------------------------------------------------------

def _make_stat_task(module_path: str, class_name: str, source_name: str):
    """Run a scraper and save to statistical_reports."""
    async def _run():
        records = await _run_scraper(module_path, class_name)
        saved = 0
        if records:
            saved = await _save_statistical_reports(records, source_name)
        await _update_data_source(source_name, saved)
        return {"status": "completed", "records_saved": saved}
    return _run_async(_run())


def _make_transparency_task(module_path: str, class_name: str, source_name: str):
    """Run a scraper and save to transparency_reports."""
    async def _run():
        records = await _run_scraper(module_path, class_name)
        saved = 0
        if records:
            saved = await _save_transparency_reports(records, source_name)
        await _update_data_source(source_name, saved)
        return {"status": "completed", "records_saved": saved}
    return _run_async(_run())


def _make_news_task(module_path: str, class_name: str, source_name: str):
    """Run a scraper and save to news_articles."""
    async def _run():
        records = await _run_scraper(module_path, class_name)
        if records:
            article_ids = await _save_news_articles(records, source_name)
            await _update_data_source(source_name, len(records))
            _enqueue_ai_processing(article_ids)
            return {
                "status": "completed",
                "articles_found": len(records),
                "saved": len(article_ids),
            }
        await _update_data_source(source_name, 0)
        return {"status": "completed", "articles_found": 0}
    return _run_async(_run())


# ---------------------------------------------------------------------------
# Phase 1: CSA scrapers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_sahil", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_sahil(self) -> dict:
    """Scrape Sahil Cruel Numbers annual reports."""
    logger.info("Scraping Sahil reports")
    return _make_stat_task("data.scrapers.government.sahil", "SahilScraper", "sahil")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_ecpat", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_ecpat(self) -> dict:
    """Scrape ECPAT country assessment for Pakistan."""
    logger.info("Scraping ECPAT")
    return _make_stat_task("data.scrapers.international.ecpat", "ECPATScraper", "ecpat")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_pahchaan", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_pahchaan(self) -> dict:
    """Scrape Pahchaan hospital-based child protection data."""
    logger.info("Scraping Pahchaan")
    return _make_stat_task("data.scrapers.government.pahchaan", "PahchaanScraper", "pahchaan")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_unicef_pakistan", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_unicef_pakistan(self) -> dict:
    """Scrape UNICEF Pakistan child protection data."""
    logger.info("Scraping UNICEF Pakistan")
    return _make_stat_task(
        "data.scrapers.international.unicef_pakistan",
        "UNICEFPakistanScraper", "unicef_pakistan",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_ncrc", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_ncrc(self) -> dict:
    """Scrape NCRC State of Children Report."""
    logger.info("Scraping NCRC")
    return _make_stat_task("data.scrapers.government.ncrc", "NCRCScraper", "ncrc")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_cpwb_punjab", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_cpwb_punjab(self) -> dict:
    """Scrape CPWB Punjab helpline 1121 statistics."""
    logger.info("Scraping CPWB Punjab")
    return _make_stat_task(
        "data.scrapers.government.cpwb_punjab", "CPWBPunjabScraper", "cpwb_punjab",
    )


# ---------------------------------------------------------------------------
# Phase 2: Online Exploitation scrapers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_ncmec", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_ncmec(self) -> dict:
    """Scrape NCMEC missing children reports."""
    logger.info("Scraping NCMEC")
    return _make_stat_task("data.scrapers.international.ncmec", "NCMECScraper", "ncmec")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_iwf_reports", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_iwf_reports(self) -> dict:
    """Scrape IWF annual reports."""
    logger.info("Scraping IWF")
    return _make_stat_task(
        "data.scrapers.international.iwf_reports", "IWFReportsScraper", "iwf_reports",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_meta_transparency", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_meta_transparency(self) -> dict:
    """Scrape Meta transparency report data."""
    logger.info("Scraping Meta Transparency")
    return _make_transparency_task(
        "data.scrapers.international.meta_transparency",
        "MetaTransparencyScraper", "meta_transparency",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_google_transparency", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_google_transparency(self) -> dict:
    """Scrape Google transparency report data."""
    logger.info("Scraping Google Transparency")
    return _make_transparency_task(
        "data.scrapers.international.google_transparency",
        "GoogleTransparencyScraper", "google_transparency",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_drf_newsletters", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_drf_newsletters(self) -> dict:
    """Scrape Digital Rights Foundation helpline stats."""
    logger.info("Scraping DRF newsletters")
    return _make_stat_task(
        "data.scrapers.government.drf_newsletters", "DRFNewslettersScraper", "drf_newsletters",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_weprotect_gta", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_weprotect_gta(self) -> dict:
    """Scrape WeProtect Global Threat Assessment."""
    logger.info("Scraping WeProtect GTA")
    return _make_stat_task(
        "data.scrapers.international.weprotect_gta", "WeProtectGTAScraper", "weprotect_gta",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_bytes_for_all", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_bytes_for_all(self) -> dict:
    """Scrape Bytes for All publications."""
    logger.info("Scraping Bytes for All")
    return _make_stat_task(
        "data.scrapers.government.bytes_for_all", "BytesForAllScraper", "bytes_for_all",
    )


# ---------------------------------------------------------------------------
# Phase 3: Child Labor scrapers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_ilostat_api", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_ilostat_api(self) -> dict:
    """Scrape ILOSTAT child labor indicators."""
    logger.info("Scraping ILOSTAT API")
    return _make_stat_task(
        "data.scrapers.international.ilostat_api", "ILOSTATAPIScraper", "ilostat_api",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_dol_annual_report", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_dol_annual_report(self) -> dict:
    """Scrape US DOL annual child labor report for Pakistan."""
    logger.info("Scraping DOL Annual Report")
    return _make_stat_task(
        "data.scrapers.international.dol_annual_report",
        "DOLAnnualReportScraper", "dol_annual_report",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_dol_tvpra", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_dol_tvpra(self) -> dict:
    """Scrape DOL TVPRA list of goods produced by child/forced labor."""
    logger.info("Scraping DOL TVPRA")
    return _make_stat_task("data.scrapers.international.dol_tvpra", "DOLTVPRAScraper", "dol_tvpra")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_labour_surveys", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_labour_surveys(self) -> dict:
    """Scrape provincial child labour survey data."""
    logger.info("Scraping Labour Surveys")
    return _make_stat_task(
        "data.scrapers.government.labour_surveys", "LabourSurveysScraper", "labour_surveys",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_zenodo_kilns", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_zenodo_kilns(self) -> dict:
    """Download Zenodo brick kiln dataset."""
    logger.info("Scraping Zenodo Kilns")
    return _make_stat_task(
        "data.scrapers.international.zenodo_kilns_scraper",
        "ZenodoKilnsScraper", "zenodo_kilns",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_bllf", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_bllf(self) -> dict:
    """Scrape BLLF bonded labour freed statistics."""
    logger.info("Scraping BLLF")
    return _make_stat_task("data.scrapers.government.bllf", "BLLFScraper", "bllf")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_brick_kiln_dashboard", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_brick_kiln_dashboard(self) -> dict:
    """Scrape Urban Unit brick kiln dashboard."""
    logger.info("Scraping Brick Kiln Dashboard")
    return _make_stat_task(
        "data.scrapers.government.brick_kiln_dashboard",
        "BrickKilnDashboardScraper", "brick_kiln_dashboard",
    )


# ---------------------------------------------------------------------------
# Phase 4: Cross-border scrapers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_ctdc_dataset", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_ctdc_dataset(self) -> dict:
    """Scrape CTDC trafficking victim dataset."""
    logger.info("Scraping CTDC Dataset")
    return _make_stat_task(
        "data.scrapers.international.ctdc_dataset", "CTDCDatasetScraper", "ctdc_dataset",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_brookings_bride", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=120,
)
def scrape_brookings_bride(self) -> dict:
    """Scrape Brookings bride trafficking research."""
    logger.info("Scraping Brookings Bride")
    return _make_stat_task(
        "data.scrapers.international.brookings_bride",
        "BrookingsBrideScraper", "brookings_bride",
    )


# ---------------------------------------------------------------------------
# Phase 5: Urdu news scrapers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_jang_urdu", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=60,
)
def scrape_news_jang_urdu(self) -> dict:
    """Scrape Jang Urdu daily news."""
    logger.info("Scraping Jang Urdu")
    return _make_news_task("data.scrapers.news.jang_urdu", "JangUrduScraper", "jang_urdu")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_express_urdu", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=60,
)
def scrape_news_express_urdu(self) -> dict:
    """Scrape Express Urdu daily news."""
    logger.info("Scraping Express Urdu")
    return _make_news_task(
        "data.scrapers.news.express_urdu", "ExpressUrduScraper", "express_urdu",
    )


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_bbc_urdu", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=60,
)
def scrape_news_bbc_urdu(self) -> dict:
    """Scrape BBC Urdu news."""
    logger.info("Scraping BBC Urdu")
    return _make_news_task("data.scrapers.news.bbc_urdu", "BBCUrduScraper", "bbc_urdu")


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_news_geo_urdu", bind=True,
    max_retries=3, autoretry_for=(Exception,), retry_backoff=60,
)
def scrape_news_geo_urdu(self) -> dict:
    """Scrape Geo Urdu news."""
    logger.info("Scraping Geo Urdu")
    return _make_news_task("data.scrapers.news.geo_urdu", "GeoUrduScraper", "geo_urdu")
