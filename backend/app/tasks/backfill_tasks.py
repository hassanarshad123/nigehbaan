"""One-time backfill tasks for historical data import."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

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


# Known Sahil "Cruel Numbers" PDF URLs (2010-2024)
SAHIL_PDF_URLS: list[dict[str, Any]] = [
    {"year": 2024, "url": "https://sahil.org/wp-content/uploads/2025/03/Cruel-Numbers-2024.pdf"},
    {"year": 2023, "url": "https://sahil.org/wp-content/uploads/2024/04/Cruel-Numbers-2023.pdf"},
    {"year": 2022, "url": "https://sahil.org/wp-content/uploads/2023/04/Cruel-Numbers-2022.pdf"},
    {"year": 2021, "url": "https://sahil.org/wp-content/uploads/2022/04/Cruel-Numbers-2021.pdf"},
    {"year": 2020, "url": "https://sahil.org/wp-content/uploads/2021/04/Cruel-Numbers-2020.pdf"},
    {"year": 2019, "url": "https://sahil.org/wp-content/uploads/2020/04/Cruel-Numbers-2019.pdf"},
    {"year": 2018, "url": "https://sahil.org/wp-content/uploads/2019/04/Cruel-Numbers-2018.pdf"},
    {"year": 2017, "url": "https://sahil.org/wp-content/uploads/2018/04/Cruel-Numbers-2017.pdf"},
    {"year": 2016, "url": "https://sahil.org/wp-content/uploads/2017/04/Cruel-Numbers-2016.pdf"},
    {"year": 2015, "url": "https://sahil.org/wp-content/uploads/2016/04/Cruel-Numbers-2015.pdf"},
    {"year": 2014, "url": "https://sahil.org/wp-content/uploads/2015/06/Cruel-Numbers-2014.pdf"},
    {"year": 2013, "url": "https://sahil.org/wp-content/uploads/2014/06/Cruel-Numbers-2013.pdf"},
    {"year": 2012, "url": "https://sahil.org/wp-content/uploads/2013/06/Cruel-Numbers-2012.pdf"},
    {"year": 2011, "url": "https://sahil.org/wp-content/uploads/2012/06/Cruel-Numbers-2011.pdf"},
    {"year": 2010, "url": "https://sahil.org/wp-content/uploads/2011/06/Cruel-Numbers-2010.pdf"},
]


@celery_app.task(
    name="app.tasks.backfill_tasks.backfill_sahil_pdfs",
    bind=True,
    max_retries=1,
)
def backfill_sahil_pdfs(self) -> dict:
    """Download and parse all Sahil 'Cruel Numbers' PDFs (2010-2024).

    One-time manual trigger, not scheduled.
    For each PDF: download -> parse -> save to statistical_reports.
    """
    logger.info("Starting Sahil PDF backfill (%d PDFs)", len(SAHIL_PDF_URLS))

    async def _run():
        import tempfile
        from pathlib import Path

        import httpx

        from app.tasks.scraping_tasks import _save_statistical_reports, _update_data_source

        total_saved = 0
        errors = []

        async with httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            headers={"User-Agent": "Nigehbaan/1.0 (Child Protection Research)"},
        ) as client:
            for pdf_info in SAHIL_PDF_URLS:
                year = pdf_info["year"]
                url = pdf_info["url"]

                try:
                    logger.info("Downloading Sahil PDF for %d: %s", year, url)
                    response = await client.get(url)

                    if response.status_code != 200:
                        logger.warning(
                            "Failed to download Sahil %d (HTTP %d)", year, response.status_code
                        )
                        errors.append({"year": year, "error": f"HTTP {response.status_code}"})
                        continue

                    # Save to temp file
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        tmp.write(response.content)
                        tmp_path = Path(tmp.name)

                    # Parse PDF
                    records = await _parse_sahil_pdf(tmp_path, year, url)
                    tmp_path.unlink(missing_ok=True)

                    if records:
                        saved = await _save_statistical_reports(records, "sahil")
                        total_saved += saved
                        logger.info("Sahil %d: saved %d records", year, saved)
                    else:
                        logger.warning("Sahil %d: no records extracted", year)

                except Exception as exc:
                    logger.error("Sahil %d backfill failed: %s", year, exc)
                    errors.append({"year": year, "error": str(exc)})

        await _update_data_source("sahil_backfill", total_saved)
        return {
            "status": "completed",
            "total_saved": total_saved,
            "errors": errors,
        }

    return _run_async(_run())


async def _parse_sahil_pdf(pdf_path, year: int, source_url: str) -> list[dict[str, Any]]:
    """Extract statistical records from a Sahil Cruel Numbers PDF."""
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber not installed, cannot parse PDFs")
        return []

    records: list[dict[str, Any]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

                # Also extract tables
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 2:
                            continue
                        # Try to parse as indicator/value pairs
                        indicator = str(row[0]).strip() if row[0] else None
                        if not indicator:
                            continue

                        for col_idx in range(1, len(row)):
                            val_str = str(row[col_idx]).strip() if row[col_idx] else ""
                            val_str = val_str.replace(",", "").replace(" ", "")
                            try:
                                value = float(val_str)
                            except (ValueError, TypeError):
                                continue

                            records.append({
                                "report_year": year,
                                "report_title": f"Sahil Cruel Numbers {year}",
                                "indicator": indicator[:200],
                                "value": value,
                                "unit": "cases",
                                "geographic_scope": "Pakistan",
                                "pdf_url": source_url,
                                "extraction_method": "pdfplumber_table",
                                "extraction_confidence": 0.7,
                            })

            # If no table data was extracted, try regex patterns on full text
            if not records and full_text:
                import re
                # Common pattern: "Category Name ... 1,234"
                pattern = re.compile(r"([A-Za-z\s/&]+?)\s*[.…]*\s*(\d[\d,]*)\s*$", re.MULTILINE)
                for match in pattern.finditer(full_text):
                    indicator = match.group(1).strip()
                    val_str = match.group(2).replace(",", "")
                    if len(indicator) > 3 and len(indicator) < 200:
                        try:
                            value = float(val_str)
                            records.append({
                                "report_year": year,
                                "report_title": f"Sahil Cruel Numbers {year}",
                                "indicator": indicator,
                                "value": value,
                                "unit": "cases",
                                "geographic_scope": "Pakistan",
                                "pdf_url": source_url,
                                "extraction_method": "regex_text",
                                "extraction_confidence": 0.5,
                            })
                        except (ValueError, TypeError):
                            continue

    except Exception as exc:
        logger.error("PDF parsing failed for Sahil %d: %s", year, exc)

    return records


@celery_app.task(
    name="app.tasks.backfill_tasks.reprocess_all_articles",
    bind=True,
    max_retries=1,
)
def reprocess_all_articles(self) -> dict:
    """Re-run AI extraction on all existing articles.

    Used after updating the OpenAI API key to reprocess articles
    that failed with the expired key.
    """
    logger.info("Starting reprocessing of all articles")

    async def _run():
        from sqlalchemy import select

        from app.database import async_session_factory
        from app.models.news_articles import NewsArticle
        from app.tasks.processing_tasks import process_article_ai

        async with async_session_factory() as session:
            result = await session.execute(
                select(NewsArticle.id).where(
                    NewsArticle.is_trafficking_relevant.is_(None)
                    | (NewsArticle.extracted_incidents.is_(None))
                )
            )
            article_ids = [row[0] for row in result.all()]

        logger.info("Found %d articles to reprocess", len(article_ids))

        for article_id in article_ids:
            process_article_ai.delay(article_id)

        return {"status": "enqueued", "articles_count": len(article_ids)}

    return _run_async(_run())
