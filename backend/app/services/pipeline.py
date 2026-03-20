"""Article processing pipeline orchestrator.

Coordinates the full flow: scrape -> save raw -> AI extract ->
geocode -> create incident -> update risk scores.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from app.config import settings
from app.services.ai_extractor import AIExtractor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessingResult:
    """Outcome of processing a single article through the pipeline."""

    article_id: int
    stage: str  # "filtered", "extracted", "geocoded", "incident_created", "error"
    is_relevant: bool
    incident_type: str | None = None
    incident_id: int | None = None
    confidence: float = 0.0
    error: str | None = None


class ArticleProcessingPipeline:
    """Orchestrates the full article processing pipeline.

    Usage::

        pipeline = ArticleProcessingPipeline()
        result = await pipeline.process_article(article_id)
    """

    def __init__(self) -> None:
        self._extractor: AIExtractor | None = None

    def _get_extractor(self) -> AIExtractor:
        """Get or create the AI extractor instance."""
        if self._extractor is None:
            self._extractor = AIExtractor(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                max_concurrent=settings.openai_max_concurrent,
            )
        return self._extractor

    async def process_article(self, article_id: int) -> ProcessingResult:
        """Run the full pipeline on a single article.

        Steps:
            1. Load article from database
            2. Keyword pre-filter (free)
            3. AI extraction via OpenAI
            4. Geocode extracted locations
            5. Create/update incident record
            6. Update article JSONB columns

        Args:
            article_id: Primary key of the news_articles row.

        Returns:
            ProcessingResult with the outcome and any created incident ID.
        """
        from sqlalchemy import select

        from app.database import async_session_factory
        from app.models.incidents import Incident
        from app.models.news_articles import NewsArticle
        from app.services.geocoder import PakistanGeocoder

        extractor = self._get_extractor()

        async with async_session_factory() as session:
            # Step 1: Load article
            result = await session.execute(
                select(NewsArticle).where(NewsArticle.id == article_id)
            )
            article = result.scalar_one_or_none()

            if article is None:
                return ProcessingResult(
                    article_id=article_id,
                    stage="error",
                    is_relevant=False,
                    error="Article not found",
                )

            title = article.title or ""
            text = article.full_text or ""

            if not text and not title:
                return ProcessingResult(
                    article_id=article_id,
                    stage="filtered",
                    is_relevant=False,
                    error="No text content",
                )

            # Step 2: Keyword pre-filter
            if not extractor.is_relevant(title, text):
                article.is_trafficking_relevant = False
                article.relevance_score = 0.0
                await session.commit()
                return ProcessingResult(
                    article_id=article_id,
                    stage="filtered",
                    is_relevant=False,
                )

            # Step 3: AI extraction
            try:
                extraction = await extractor.extract_structured(
                    title=title,
                    text=text,
                    source_url=article.url,
                )
            except Exception as exc:
                logger.error("AI extraction failed for article %d: %s", article_id, exc)
                return ProcessingResult(
                    article_id=article_id,
                    stage="error",
                    is_relevant=False,
                    error=f"AI extraction failed: {exc}",
                )

            # Update article with extraction results
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

            if not extraction.is_relevant or not extraction.incident_type:
                await session.commit()
                return ProcessingResult(
                    article_id=article_id,
                    stage="extracted",
                    is_relevant=extraction.is_relevant,
                    incident_type=extraction.incident_type,
                    confidence=extraction.confidence,
                )

            # Step 4: Geocode
            geometry = None
            district_pcode = None
            location_detail = None
            geocode_confidence = None

            if extraction.locations:
                best_loc = extraction.locations[0]
                location_detail = best_loc.name

                geocoder = PakistanGeocoder(
                    gazetteer_path="data/config/gazetteer/pakistan_districts.json"
                )
                geo_result = await geocoder.geocode(best_loc.name)

                if geo_result:
                    lat, lon, confidence = geo_result
                    from geoalchemy2.elements import WKTElement
                    geometry = WKTElement(f"POINT({lon} {lat})", srid=4326)
                    geocode_confidence = confidence
                    district_pcode = geocoder.match_district(best_loc.name)

            # Step 5: Create incident
            incident_date = None
            if extraction.incident_date:
                try:
                    incident_date = datetime.strptime(
                        extraction.incident_date, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass

            effective_date = incident_date or article.published_date

            incident = Incident(
                source_type="news",
                source_id=str(article.id),
                source_url=article.url,
                incident_date=effective_date,
                report_date=article.published_date,
                year=effective_date.year if effective_date else None,
                month=effective_date.month if effective_date else None,
                district_pcode=district_pcode,
                location_detail=location_detail,
                geometry=geometry,
                geocode_confidence=geocode_confidence,
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
            await session.flush()
            incident_id = incident.id

            await session.commit()

            if geometry:
                stage = "incident_created"
            elif location_detail:
                stage = "geocoded"
            else:
                stage = "extracted"

            return ProcessingResult(
                article_id=article_id,
                stage=stage,
                is_relevant=True,
                incident_type=extraction.incident_type,
                incident_id=incident_id,
                confidence=extraction.confidence,
            )

    async def process_batch(
        self,
        article_ids: list[int],
    ) -> list[ProcessingResult]:
        """Process multiple articles through the pipeline.

        Args:
            article_ids: List of article primary keys.

        Returns:
            List of ProcessingResult in the same order.
        """
        results: list[ProcessingResult] = []
        for article_id in article_ids:
            try:
                result = await self.process_article(article_id)
                results.append(result)
            except Exception as exc:
                logger.error("Pipeline error for article %d: %s", article_id, exc)
                results.append(ProcessingResult(
                    article_id=article_id,
                    stage="error",
                    is_relevant=False,
                    error=str(exc),
                ))
        return results
