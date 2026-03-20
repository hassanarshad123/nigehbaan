"""Celery tasks for importing data from external sources."""

from __future__ import annotations

import asyncio
import logging

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


@celery_app.task(
    name="app.tasks.import_tasks.import_external_judgments",
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=300,
)
def import_external_judgments(self, batch_size: int = 100) -> dict:
    """Import trafficking-related judgments from external Neon DB.

    Processes in batches for memory safety on t3.medium instances.
    Idempotent via ON CONFLICT (source_url) DO NOTHING.

    Args:
        batch_size: Number of rows to process per batch.
    """
    logger.info("Starting external judgment import (batch_size=%d)", batch_size)

    async def _run():
        from app.config import settings

        if not settings.external_judgments_db_url:
            logger.warning("EXTERNAL_JUDGMENTS_DB_URL not configured, skipping import")
            return {"status": "skipped", "reason": "no_external_db_url"}

        from app.services.judgment_importer import JudgmentImporter

        importer = JudgmentImporter()
        result = await importer.import_trafficking_judgments(batch_size=batch_size)

        logger.info(
            "Judgment import complete: fetched=%d, saved=%d",
            result["total_fetched"],
            result["total_saved"],
        )

        # Update data source record
        from app.tasks.scraping_tasks import _update_data_source
        await _update_data_source("external_judgments", result["total_saved"])

        return {
            "status": "completed",
            "total_fetched": result["total_fetched"],
            "total_saved": result["total_saved"],
        }

    return _run_async(_run())
