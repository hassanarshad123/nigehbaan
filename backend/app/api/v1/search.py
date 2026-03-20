"""Global search API endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.boundaries import Boundary
from app.models.court_judgments import CourtJudgment
from app.models.incidents import Incident
from app.models.news_articles import NewsArticle
from app.schemas.search import SearchResult

router = APIRouter()


@router.get("/", response_model=list[SearchResult])
async def global_search(
    q: str = Query(..., min_length=2, max_length=200, description="Search query string"),
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    """Search across incidents, judgments, articles, and districts.

    Uses ILIKE pattern matching on key text columns. Results are ranked
    by match quality: exact > starts-with > contains.
    """
    pattern = f"%{q}%"
    results: list[SearchResult] = []

    # 1. Incidents — match on location_detail, raw_text
    inc_result = await db.execute(
        select(
            Incident.id,
            Incident.location_detail,
            Incident.raw_text,
            Incident.district_pcode,
            Incident.year,
        )
        .where(
            Incident.location_detail.ilike(pattern)
            | Incident.raw_text.ilike(pattern)
        )
        .limit(10)
    )
    for row in inc_result.all():
        title = row.location_detail or "Incident"
        snippet = (row.raw_text or "")[:200]
        results.append(SearchResult(
            id=row.id,
            type="incident",
            title=title,
            snippet=snippet,
            relevanceScore=1.0,
            districtPcode=row.district_pcode,
            year=row.year,
        ))

    # 2. Court judgments — match on case_number, appellant, respondent
    jdg_result = await db.execute(
        select(
            CourtJudgment.id,
            CourtJudgment.case_number,
            CourtJudgment.appellant,
            CourtJudgment.respondent,
            CourtJudgment.incident_district_pcode,
            func.extract("year", CourtJudgment.judgment_date).label("year"),
        )
        .where(
            CourtJudgment.case_number.ilike(pattern)
            | CourtJudgment.appellant.ilike(pattern)
            | CourtJudgment.respondent.ilike(pattern)
        )
        .limit(10)
    )
    for row in jdg_result.all():
        title = row.case_number or "Court Judgment"
        snippet = f"{row.appellant or ''} v. {row.respondent or ''}"[:200]
        results.append(SearchResult(
            id=row.id,
            type="judgment",
            title=title,
            snippet=snippet,
            relevanceScore=1.0,
            districtPcode=row.incident_district_pcode,
            year=int(row.year) if row.year else None,
        ))

    # 3. News articles — match on title, full_text
    art_result = await db.execute(
        select(
            NewsArticle.id,
            NewsArticle.title,
            NewsArticle.full_text,
            func.extract("year", NewsArticle.published_date).label("year"),
        )
        .where(
            NewsArticle.title.ilike(pattern)
            | NewsArticle.full_text.ilike(pattern)
        )
        .limit(10)
    )
    for row in art_result.all():
        title = row.title or "News Article"
        snippet = (row.full_text or "")[:200]
        results.append(SearchResult(
            id=row.id,
            type="article",
            title=title,
            snippet=snippet,
            relevanceScore=1.0,
            districtPcode=None,
            year=int(row.year) if row.year else None,
        ))

    # 4. Boundaries — match on name_en, name_ur
    bnd_result = await db.execute(
        select(
            Boundary.id,
            Boundary.name_en,
            Boundary.name_ur,
            Boundary.pcode,
        )
        .where(
            Boundary.name_en.ilike(pattern)
            | Boundary.name_ur.ilike(pattern)
        )
        .limit(10)
    )
    for row in bnd_result.all():
        results.append(SearchResult(
            id=row.id,
            type="district",
            title=row.name_en,
            snippet=f"{row.name_en} ({row.name_ur or ''})"[:200],
            relevanceScore=1.0,
            districtPcode=row.pcode,
            year=None,
        ))

    # Sort by relevance: exact match > starts-with > contains
    q_lower = q.lower()

    def _relevance(r: SearchResult) -> int:
        t = r.title.lower()
        if t == q_lower:
            return 0
        if t.startswith(q_lower):
            return 1
        return 2

    results.sort(key=_relevance)
    return results
