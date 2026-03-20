"""Celery tasks for data processing, NLP, AI extraction, and scoring.

The key task is process_article_ai which runs the full pipeline:
keyword pre-filter -> OpenAI extraction -> geocoding -> incident creation.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from app.config import settings
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


# ---------------------------------------------------------------------------
# Core AI processing task
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.processing_tasks.process_article_ai",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=30,
)
def process_article_ai(self, article_id: int) -> dict:
    """Run the full AI extraction pipeline on a single news article.

    Pipeline:
        1. Load article from news_articles
        2. Keyword pre-filter (free)
        3. AIExtractor.extract_structured() via OpenAI (if relevant)
        4. Update JSONB columns on news_articles
        5. Create Incident record if relevant
        6. Geocode via PakistanGeocoder

    Args:
        article_id: Primary key of the news_articles row.
    """
    logger.info("Processing article %d with AI", article_id)

    async def _run():
        from app.database import async_session_factory
        from app.models.incidents import Incident
        from app.models.news_articles import NewsArticle
        from app.services.ai_extractor import AIExtractor
        from app.services.geocoder import PakistanGeocoder

        async with async_session_factory() as session:
            # 1. Load article
            from sqlalchemy import select
            result = await session.execute(
                select(NewsArticle).where(NewsArticle.id == article_id)
            )
            article = result.scalar_one_or_none()

            if article is None:
                logger.warning("Article %d not found", article_id)
                return {"status": "not_found", "article_id": article_id}

            title = article.title or ""
            text = article.full_text or ""

            if not text and not title:
                return {"status": "skipped", "article_id": article_id, "reason": "no_text"}

            # 2. Keyword pre-filter (free, no API call)
            extractor = AIExtractor(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                max_concurrent=settings.openai_max_concurrent,
            )

            if not extractor.is_relevant(title, text):
                article.is_trafficking_relevant = False
                article.relevance_score = 0.0
                await session.commit()
                return {
                    "status": "filtered",
                    "article_id": article_id,
                    "reason": "keyword_pre_filter",
                }

            # 3. AI extraction via OpenAI (detect Urdu sources)
            urdu_sources = {"jang_urdu", "express_urdu", "bbc_urdu", "geo_urdu"}
            is_urdu = article.source_name in urdu_sources

            if is_urdu:
                logger.info(
                    "Urdu extraction for article %d (source: %s)",
                    article_id, article.source_name,
                )
                extraction = await extractor.extract_from_urdu(
                    title=title,
                    text=text,
                    source_url=article.url,
                )
            else:
                extraction = await extractor.extract_structured(
                    title=title,
                    text=text,
                    source_url=article.url,
                )

            # 4. Update article JSONB columns
            article.is_trafficking_relevant = extraction.is_relevant
            article.relevance_score = extraction.confidence

            article.extracted_incidents = {
                "incident_type": extraction.incident_type,
                "sub_type": extraction.sub_type,
                "victim_count": extraction.victim_count,
                "victim_age_min": extraction.victim_age_min,
                "victim_age_max": extraction.victim_age_max,
                "victim_gender": extraction.victim_gender,
                "perpetrator_type": extraction.perpetrator_type,
                "ppc_sections": extraction.ppc_sections,
                "incident_date": extraction.incident_date,
                "confidence": extraction.confidence,
            }

            article.extracted_locations = [
                {
                    "name": loc.name,
                    "district": loc.district,
                    "province": loc.province,
                    "confidence": loc.confidence,
                }
                for loc in extraction.locations
            ]

            article.extracted_entities = extraction.raw_extraction

            # 5. Create Incident if relevant (with duplicate check)
            if extraction.is_relevant and extraction.incident_type:
                # Check for existing incident from same article
                from sqlalchemy import select as sa_select
                existing = await session.execute(
                    sa_select(Incident.id).where(
                        Incident.source_type == "news",
                        Incident.source_id == str(article.id),
                    )
                )
                if existing.scalar_one_or_none() is not None:
                    logger.info(
                        "Incident already exists for article %d, skipping creation",
                        article_id,
                    )
                    await session.commit()
                    return {
                        "status": "completed",
                        "article_id": article_id,
                        "is_relevant": extraction.is_relevant,
                        "incident_type": extraction.incident_type,
                        "confidence": extraction.confidence,
                        "note": "incident_already_exists",
                    }

                # Parse incident date
                incident_date = None
                if extraction.incident_date:
                    try:
                        incident_date = datetime.strptime(
                            extraction.incident_date, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        pass

                # Determine location info
                district_pcode = None
                location_detail = None
                geometry = None

                if extraction.locations:
                    best_loc = extraction.locations[0]
                    location_detail = best_loc.name

                    # 6. Geocode
                    geocoder = PakistanGeocoder(
                        gazetteer_path="data/config/gazetteer/pakistan_districts.json"
                    )
                    geo_result = await geocoder.geocode(best_loc.name)

                    if geo_result:
                        lat, lon, confidence = geo_result
                        from geoalchemy2.elements import WKTElement
                        geometry = WKTElement(
                            f"POINT({lon} {lat})", srid=4326
                        )
                        # Try to match district
                        district_pcode = geocoder.match_district(best_loc.name)

                incident = Incident(
                    source_type="news",
                    source_id=str(article.id),
                    source_url=article.url,
                    incident_date=incident_date or article.published_date or None,
                    report_date=article.published_date,
                    year=(
                        (incident_date or article.published_date).year
                        if (incident_date or article.published_date) else None
                    ),
                    month=(
                        (incident_date or article.published_date).month
                        if (incident_date or article.published_date) else None
                    ),
                    district_pcode=district_pcode,
                    location_detail=location_detail,
                    geometry=geometry,
                    incident_type=extraction.incident_type,
                    sub_type=extraction.sub_type,
                    victim_count=extraction.victim_count,
                    victim_gender=extraction.victim_gender,
                    victim_age_min=extraction.victim_age_min,
                    victim_age_max=extraction.victim_age_max,
                    perpetrator_type=extraction.perpetrator_type,
                    extraction_confidence=extraction.confidence,
                    raw_text=text[:5000],
                )
                session.add(incident)

            await session.commit()

            return {
                "status": "completed",
                "article_id": article_id,
                "is_relevant": extraction.is_relevant,
                "incident_type": extraction.incident_type,
                "confidence": extraction.confidence,
            }

    return _run_async(_run())


# ---------------------------------------------------------------------------
# PDF processing
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.processing_tasks.process_pdf",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def process_pdf(self, s3_key: str) -> dict:
    """Download a PDF from S3, extract text and tables, store results.

    Args:
        s3_key: The S3 object key for the PDF file.
    """
    logger.info("Processing PDF: %s", s3_key)

    async def _run():
        import tempfile
        from pathlib import Path

        import boto3

        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed")
            return {"status": "error", "error": "pdfplumber not installed"}

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            s3.download_file(settings.s3_bucket, s3_key, tmp.name)
            tmp_path = Path(tmp.name)

        pages_processed = 0
        extracted_text = []

        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
                    pages_processed += 1

        tmp_path.unlink(missing_ok=True)

        full_text = "\n\n".join(extracted_text)

        if full_text:
            from app.services.ai_extractor import AIExtractor

            extractor = AIExtractor(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
            )
            extraction = await extractor.extract_structured(
                title=s3_key,
                text=full_text[:8000],
                source_url=f"s3://{settings.s3_bucket}/{s3_key}",
            )
            return {
                "status": "completed",
                "s3_key": s3_key,
                "pages_processed": pages_processed,
                "is_relevant": extraction.is_relevant,
            }

        return {"status": "completed", "s3_key": s3_key, "pages_processed": 0}

    return _run_async(_run())


# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.processing_tasks.geocode_incidents",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def geocode_incidents(self, batch_size: int = 100) -> dict:
    """Geocode incidents that have location_detail but no geometry.

    Args:
        batch_size: Number of incidents to geocode in this batch.
    """
    logger.info("Geocoding incidents (batch_size=%d)", batch_size)

    async def _run():
        from sqlalchemy import select

        from app.database import async_session_factory
        from app.models.incidents import Incident
        from app.services.geocoder import PakistanGeocoder

        geocoder = PakistanGeocoder(
            gazetteer_path="data/config/gazetteer/pakistan_districts.json"
        )

        geocoded = 0
        failed = 0

        async with async_session_factory() as session:
            result = await session.execute(
                select(Incident)
                .where(Incident.geometry.is_(None))
                .where(Incident.location_detail.isnot(None))
                .limit(batch_size)
            )
            incidents = result.scalars().all()

            for incident in incidents:
                geo_result = await geocoder.geocode(incident.location_detail)
                if geo_result:
                    lat, lon, confidence = geo_result
                    from geoalchemy2.elements import WKTElement
                    incident.geometry = WKTElement(
                        f"POINT({lon} {lat})", srid=4326
                    )
                    incident.geocode_confidence = confidence

                    if not incident.district_pcode:
                        incident.district_pcode = geocoder.match_district(
                            incident.location_detail
                        )

                    geocoded += 1
                else:
                    failed += 1

            await session.commit()

        return {"status": "completed", "geocoded": geocoded, "failed": failed}

    return _run_async(_run())


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.processing_tasks.calculate_risk_scores",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def calculate_risk_scores(self) -> dict:
    """Recalculate trafficking_risk_score for all districts."""
    logger.info("Calculating risk scores")

    async def _run():
        from sqlalchemy import select

        from app.database import async_session_factory
        from app.models.vulnerability import VulnerabilityIndicator
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        districts_scored = 0

        async with async_session_factory() as session:
            result = await session.execute(
                select(VulnerabilityIndicator)
            )
            indicators_list = result.scalars().all()

            for vi in indicators_list:
                indicators = {
                    "poverty_headcount_ratio": vi.poverty_headcount_ratio,
                    "out_of_school_rate": vi.school_dropout_rate,
                    "brick_kiln_density": vi.brick_kiln_density_per_sqkm,
                    "child_labor_rate": vi.child_labor_rate,
                    "child_marriage_rate": vi.child_marriage_rate,
                    "refugee_population_ratio": vi.refugee_population,
                    "flood_affected_pct": vi.flood_affected_pct,
                }

                score = await scorer.calculate_score(
                    vi.district_pcode,
                    indicators,
                )
                vi.trafficking_risk_score = score
                districts_scored += 1

            await session.commit()

        return {"status": "completed", "districts_scored": districts_scored}

    return _run_async(_run())


# ---------------------------------------------------------------------------
# NLP pipeline (legacy, still available)
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.processing_tasks.run_nlp_pipeline",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=30,
)
def run_nlp_pipeline(self, article_id: int) -> dict:
    """Run the keyword-based NLP pipeline on a single news article.

    For articles where AI extraction is not available or as a fallback.

    Args:
        article_id: The primary key of the news_articles row.
    """
    logger.info("Running NLP pipeline on article %d", article_id)

    async def _run():
        from sqlalchemy import select

        from app.database import async_session_factory
        from app.models.news_articles import NewsArticle
        from app.services.nlp_pipeline import TraffickingNLPPipeline

        pipeline = TraffickingNLPPipeline()

        async with async_session_factory() as session:
            result = await session.execute(
                select(NewsArticle).where(NewsArticle.id == article_id)
            )
            article = result.scalar_one_or_none()

            if article is None:
                return {"status": "not_found", "article_id": article_id}

            text = f"{article.title or ''} {article.full_text or ''}"

            is_relevant, confidence = await pipeline.classify_relevance(text)
            entities = await pipeline.extract_entities(text)

            article.is_trafficking_relevant = is_relevant
            article.relevance_score = confidence
            article.extracted_entities = entities

            await session.commit()

        return {
            "status": "completed",
            "article_id": article_id,
            "is_relevant": is_relevant,
        }

    return _run_async(_run())


# ---------------------------------------------------------------------------
# Court judgment processing
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.processing_tasks.process_court_judgment",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=30,
)
def process_court_judgment(self, judgment_id: int) -> dict:
    """Create an Incident record from a court judgment.

    When a court judgment is imported, create a corresponding Incident
    with source_type='court', geocode it, and enqueue risk score recalculation.
    Follows the pattern of process_article_ai.

    Args:
        judgment_id: Primary key of the court_judgments row.
    """
    logger.info("Processing court judgment %d", judgment_id)

    async def _run():
        from sqlalchemy import select

        from app.database import async_session_factory
        from app.models.court_judgments import CourtJudgment
        from app.models.incidents import Incident
        from app.services.geocoder import PakistanGeocoder

        async with async_session_factory() as session:
            result = await session.execute(
                select(CourtJudgment).where(CourtJudgment.id == judgment_id)
            )
            judgment = result.scalar_one_or_none()
            if judgment is None:
                return {"status": "not_found", "judgment_id": judgment_id}

            # Check for existing incident from same judgment
            existing = await session.execute(
                select(Incident.id).where(
                    Incident.source_type == "court",
                    Incident.source_id == str(judgment.id),
                )
            )
            if existing.scalar_one_or_none() is not None:
                return {"status": "already_exists", "judgment_id": judgment_id}

            # Determine incident type from PPC sections
            incident_type = _classify_court_incident(judgment.ppc_sections)

            # Geocode using court name for location
            geometry = None
            district_pcode = judgment.incident_district_pcode
            location_detail = judgment.court_name

            if location_detail and not district_pcode:
                geocoder = PakistanGeocoder(
                    gazetteer_path="data/config/gazetteer/pakistan_districts.json"
                )
                geo_result = await geocoder.geocode(location_detail)
                if geo_result:
                    lat, lon, confidence = geo_result
                    from geoalchemy2.elements import WKTElement
                    geometry = WKTElement(f"POINT({lon} {lat})", srid=4326)
                    district_pcode = geocoder.match_district(location_detail)

            incident = Incident(
                source_type="court",
                source_id=str(judgment.id),
                source_url=judgment.source_url,
                incident_date=judgment.judgment_date,
                report_date=judgment.judgment_date,
                year=judgment.judgment_date.year if judgment.judgment_date else None,
                month=judgment.judgment_date.month if judgment.judgment_date else None,
                district_pcode=district_pcode,
                location_detail=location_detail,
                geometry=geometry,
                incident_type=incident_type,
                victim_count=1,
                extraction_confidence=judgment.nlp_confidence or 0.6,
                raw_text=(judgment.judgment_text or "")[:5000],
            )

            if judgment.verdict == "convicted":
                incident.case_status = "convicted"
                incident.conviction = True
            elif judgment.verdict == "acquitted":
                incident.case_status = "acquitted"
                incident.conviction = False

            session.add(incident)
            await session.commit()

            return {
                "status": "completed",
                "judgment_id": judgment_id,
                "incident_type": incident_type,
            }

    return _run_async(_run())


def _classify_court_incident(ppc_sections: list[str] | None) -> str:
    """Classify incident type based on PPC sections."""
    if not ppc_sections:
        return "trafficking"

    sections = set(s.replace("-", "").upper() for s in ppc_sections)

    if any(s in sections for s in ("364A", "364", "365")):
        return "kidnapping"
    if any(s in sections for s in ("370", "371", "371A", "371B")):
        return "trafficking"
    if any(s in sections for s in ("377",)):
        return "sexual_abuse"
    if any(s in sections for s in ("374",)):
        return "forced_labor"
    return "trafficking"


# ---------------------------------------------------------------------------
# Vulnerability indicators
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.processing_tasks.update_vulnerability_indicators",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def update_vulnerability_indicators(self) -> dict:
    """Refresh vulnerability indicators from latest data sources."""
    logger.info("Updating vulnerability indicators")

    async def _run():
        from sqlalchemy import func, select

        from app.database import async_session_factory
        from app.models.incidents import Incident
        from app.models.statistical_reports import StatisticalReport
        from app.models.vulnerability import VulnerabilityIndicator

        districts_updated = 0

        async with async_session_factory() as session:
            # Get incident counts per district
            result = await session.execute(
                select(
                    Incident.district_pcode,
                    func.count(Incident.id).label("count"),
                )
                .where(Incident.district_pcode.isnot(None))
                .group_by(Incident.district_pcode)
            )
            incident_counts = {row[0]: row[1] for row in result.all()}

            # Fetch national-level stats from statistical_reports to enrich indicators
            stat_overrides: dict[str, float] = {}
            stat_queries = [
                ("worldbank_api", "poverty_headcount_ratio", "SI.POV.NAHC"),
                ("worldbank_api", "out_of_school_rate", "SE.PRM.UNER.ZS"),
                ("ilostat_api", "child_labor_rate", None),
                ("unhcr_api", "refugee_population_total", None),
            ]
            for source_name, key, indicator_filter in stat_queries:
                stmt = (
                    select(StatisticalReport.value)
                    .where(StatisticalReport.source_name == source_name)
                    .order_by(StatisticalReport.report_year.desc())
                    .limit(1)
                )
                if indicator_filter:
                    stmt = stmt.where(StatisticalReport.indicator == indicator_filter)
                stat_result = await session.execute(stmt)
                val = stat_result.scalar_one_or_none()
                if val is not None:
                    stat_overrides[key] = val

            # Update vulnerability indicators with incident-based risk
            vi_result = await session.execute(
                select(VulnerabilityIndicator)
            )
            for vi in vi_result.scalars().all():
                count = incident_counts.get(vi.district_pcode, 0)
                # Compute incident rate per 100k (use population_under_18 if available)
                population = vi.population_under_18 or 100_000
                incident_rate = (count / population) * 100_000 if population > 0 else 0.0

                # Apply national-level overrides where district-level data is missing
                poverty = vi.poverty_headcount_ratio
                if poverty is None and "poverty_headcount_ratio" in stat_overrides:
                    poverty = stat_overrides["poverty_headcount_ratio"]

                dropout = vi.school_dropout_rate
                if dropout is None and "out_of_school_rate" in stat_overrides:
                    dropout = stat_overrides["out_of_school_rate"]

                child_labor = vi.child_labor_rate
                if child_labor is None and "child_labor_rate" in stat_overrides:
                    child_labor = stat_overrides["child_labor_rate"]

                refugee_pop = vi.refugee_population
                if refugee_pop is None and "refugee_population_total" in stat_overrides:
                    # Distribute national refugee total proportionally
                    refugee_pop = stat_overrides["refugee_population_total"] / 160.0

                # Recalculate risk score incorporating incident rate
                from app.services.risk_scorer import RiskScorer
                scorer = RiskScorer()
                indicators = {
                    "incident_rate_per_100k": incident_rate,
                    "poverty_headcount_ratio": poverty,
                    "out_of_school_rate": dropout,
                    "brick_kiln_density": vi.brick_kiln_density_per_sqkm,
                    "child_labor_rate": child_labor,
                    "child_marriage_rate": vi.child_marriage_rate,
                    "refugee_population_ratio": refugee_pop,
                    "flood_affected_pct": vi.flood_affected_pct,
                }
                score = await scorer.calculate_score(vi.district_pcode, indicators)
                vi.trafficking_risk_score = score
                logger.info(
                    "District %s: %d incidents, rate=%.2f/100k, risk_score=%.2f",
                    vi.district_pcode, count, incident_rate, score,
                )
                districts_updated += 1

            await session.commit()

        return {"status": "completed", "districts_updated": districts_updated}

    return _run_async(_run())
