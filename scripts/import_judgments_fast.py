"""Fast court judgment import - uses head_notes filter (no slow full_text ILIKE).

Generates synthetic source_url from Neon UUID since source_url is NULL in source DB.
"""

import asyncio
import re
import ssl
import sys

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import async_session_factory
from app.models.court_judgments import CourtJudgment

PPC_RE = re.compile(
    r"(?:section|S\.?)\s*(36[4-5](?:-?[A-Z])?|37[0-1](?:-?[A-Z])?|37[2-7]|489|292)",
    re.IGNORECASE,
)
VERDICT_PATTERNS = {
    "convicted": re.compile(
        r"\b(?:convicted|conviction|sentenced|guilty|upheld conviction)\b", re.I
    ),
    "acquitted": re.compile(
        r"\b(?:acquitted|acquittal|not guilty|benefit of doubt)\b", re.I
    ),
    "dismissed": re.compile(
        r"\b(?:dismissed|dismissal|rejected|petition dismissed)\b", re.I
    ),
}

FAST_QUERY = text(
    """
    SELECT id, citation, court_name, bench, judges, judgment_date,
           petitioner, respondent, head_notes, full_text, source_url, quality_score
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
)


async def run():
    from app.config import settings

    neon_url = settings.external_judgments_db_url
    if not neon_url:
        print("ERROR: EXTERNAL_JUDGMENTS_DB_URL not set")
        sys.exit(1)

    # Convert to asyncpg URL and strip sslmode
    if neon_url.startswith("postgresql://"):
        neon_url = "postgresql+asyncpg://" + neon_url[len("postgresql://") :]
    neon_url = neon_url.split("?")[0]  # strip query params

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    engine = create_async_engine(
        neon_url, connect_args={"ssl": ssl_ctx}, pool_timeout=120
    )

    total_fetched = 0
    total_saved = 0
    offset = 0
    batch_size = 200

    while True:
        async with engine.connect() as conn:
            result = await conn.execute(
                FAST_QUERY, {"limit": batch_size, "offset": offset}
            )
            rows = result.mappings().all()

        if not rows:
            break

        total_fetched += len(rows)

        async with async_session_factory() as session:
            for row in rows:
                row = dict(row)
                full_text = row.get("full_text") or ""
                head_notes = row.get("head_notes") or ""
                combined = head_notes + "\n" + full_text

                ppc = sorted(set(PPC_RE.findall(combined))) or None
                verdict = None
                tail = full_text[-5000:] if full_text else ""
                for v, pat in VERDICT_PATTERNS.items():
                    if pat.search(tail):
                        verdict = v
                        break

                judges = row.get("judges")
                judge_names = judges if isinstance(judges, list) else None

                neon_id = str(row.get("id"))
                source_url = row.get("source_url") or (
                    "neon://pakistan_judgments/" + neon_id
                )

                try:
                    stmt = (
                        pg_insert(CourtJudgment)
                        .values(
                            case_number=row.get("citation"),
                            court_name=row.get("court_name"),
                            court_bench=row.get("bench"),
                            judge_names=judge_names,
                            judgment_date=row.get("judgment_date"),
                            appellant=row.get("petitioner"),
                            respondent=row.get("respondent"),
                            ppc_sections=ppc,
                            is_trafficking_related=True,
                            verdict=verdict,
                            judgment_text=full_text[:50000] if full_text else None,
                            source_url=source_url,
                            nlp_confidence=row.get("quality_score"),
                        )
                        .on_conflict_do_nothing(
                            constraint="uq_court_judgment_source_url"
                        )
                    )
                    r = await session.execute(stmt)
                    if r.rowcount > 0:
                        total_saved += 1
                except Exception as e:
                    print("Error: " + str(e), file=sys.stderr, flush=True)
            await session.commit()

        offset += batch_size
        print(
            "Progress: fetched="
            + str(total_fetched)
            + ", saved="
            + str(total_saved),
            flush=True,
        )

    await engine.dispose()
    print(
        "DONE: fetched=" + str(total_fetched) + ", saved=" + str(total_saved),
        flush=True,
    )


asyncio.run(run())
