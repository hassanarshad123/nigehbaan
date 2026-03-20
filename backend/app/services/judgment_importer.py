"""Import trafficking-related court judgments from an external Neon DB.

CRITICAL: This service connects to a READ-ONLY external database.
Never write, update, or delete on the source DB.
"""

from __future__ import annotations

import logging
import re
import ssl
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

# PPC sections relevant to trafficking / child abuse
PPC_SECTION_PATTERN = re.compile(
    r"(?:section|S\.?)\s*(36[4-5](?:-?[A-Z])?|37[0-1](?:-?[A-Z])?|37[2-7]|489|292)",
    re.IGNORECASE,
)

VERDICT_PATTERNS = {
    "convicted": re.compile(
        r"\b(?:convicted|convict(?:ed|ion)|sentenced|guilty|upheld conviction)\b",
        re.IGNORECASE,
    ),
    "acquitted": re.compile(
        r"\b(?:acquit(?:ted|tal)|not guilty|set aside conviction|benefit of doubt)\b",
        re.IGNORECASE,
    ),
    "dismissed": re.compile(
        r"\b(?:dismiss(?:ed|al)|rejected|petition dismissed|appeal dismissed)\b",
        re.IGNORECASE,
    ),
}

FILTER_QUERY = """
SELECT id, citation, court_name, bench, judges, judgment_date,
       petitioner, respondent, head_notes, full_text, source_url,
       quality_score
FROM pakistan_judgments
WHERE head_notes ILIKE '%trafficking%'
   OR head_notes ILIKE '%child%abuse%'
   OR head_notes ILIKE '%kidnap%'
   OR head_notes ILIKE '%bonded labour%'
   OR head_notes ILIKE '%child labour%'
   OR head_notes ILIKE '%section 370%'
   OR head_notes ILIKE '%section 371%'
   OR head_notes ILIKE '%section 364%'
   OR head_notes ILIKE '%section 365%'
ORDER BY id
LIMIT :limit OFFSET :offset
"""


def _make_async_url(url: str) -> str:
    """Convert postgresql:// URL to postgresql+asyncpg:// and strip sslmode."""
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params.pop("sslmode", None)
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))


def _extract_ppc_sections(text: str) -> list[str]:
    """Extract PPC section numbers from judgment text."""
    matches = PPC_SECTION_PATTERN.findall(text or "")
    return sorted(set(matches)) if matches else []


def _extract_verdict(text: str) -> str | None:
    """Infer verdict from judgment text keywords."""
    if not text:
        return None
    # Check last 5000 chars (conclusion is usually at the end)
    tail = text[-5000:]
    for verdict, pattern in VERDICT_PATTERNS.items():
        if pattern.search(tail):
            return verdict
    return None


def _transform_judgment(row: dict[str, Any]) -> dict[str, Any]:
    """Transform a source DB row into a court_judgments record."""
    head_notes = row.get("head_notes") or ""
    full_text = row.get("full_text") or ""
    combined_text = f"{head_notes}\n{full_text}"

    ppc_sections = _extract_ppc_sections(combined_text)
    verdict = _extract_verdict(full_text)

    judges_raw = row.get("judges")
    judge_names = judges_raw if isinstance(judges_raw, list) else None

    return {
        "case_number": row.get("citation"),
        "court_name": row.get("court_name"),
        "court_bench": row.get("bench"),
        "judge_names": judge_names,
        "judgment_date": row.get("judgment_date"),
        "appellant": row.get("petitioner"),
        "respondent": row.get("respondent"),
        "ppc_sections": ppc_sections if ppc_sections else None,
        "is_trafficking_related": True,
        "verdict": verdict,
        "judgment_text": full_text[:50000] if full_text else None,
        "source_url": row.get("source_url"),
        "nlp_confidence": row.get("quality_score"),
    }


class JudgmentImporter:
    """Import trafficking-related judgments from external Neon DB."""

    def __init__(self, external_db_url: str | None = None):
        url = external_db_url or settings.external_judgments_db_url
        if not url:
            raise ValueError("EXTERNAL_JUDGMENTS_DB_URL is not configured")

        async_url = _make_async_url(url)
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        self._engine = create_async_engine(
            async_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
            connect_args={"ssl": ssl_ctx},
        )

    async def import_trafficking_judgments(self, batch_size: int = 100) -> dict[str, int]:
        """Query external DB, transform, and upsert into local court_judgments.

        Returns dict with total_fetched and total_saved counts.
        """
        from app.database import async_session_factory
        from app.models.court_judgments import CourtJudgment

        total_fetched = 0
        total_saved = 0
        offset = 0

        while True:
            # Read from external DB (READ ONLY)
            async with self._engine.connect() as ext_conn:
                result = await ext_conn.execute(
                    text(FILTER_QUERY),
                    {"limit": batch_size, "offset": offset},
                )
                rows = result.mappings().all()

            if not rows:
                break

            total_fetched += len(rows)
            logger.info(
                "Fetched batch of %d judgments (offset=%d)", len(rows), offset
            )

            # Transform and upsert into local DB
            async with async_session_factory() as session:
                for row in rows:
                    row_dict = dict(row)
                    record = _transform_judgment(row_dict)
                    # Generate synthetic URL from Neon UUID if source_url is NULL
                    source_url = record.get("source_url")
                    if not source_url:
                        neon_id = str(row_dict.get("id", ""))
                        if not neon_id:
                            continue
                        source_url = f"neon://pakistan_judgments/{neon_id}"
                        record["source_url"] = source_url

                    try:
                        stmt = pg_insert(CourtJudgment).values(**record).on_conflict_do_nothing(
                            constraint="uq_court_judgment_source_url",
                        )
                        insert_result = await session.execute(stmt)
                        if insert_result.rowcount > 0:
                            total_saved += 1
                    except Exception as exc:
                        logger.warning("Failed to upsert judgment: %s", exc)

                await session.commit()

            offset += batch_size
            logger.info("Progress: fetched=%d, saved=%d", total_fetched, total_saved)

        await self._engine.dispose()
        return {"total_fetched": total_fetched, "total_saved": total_saved}
