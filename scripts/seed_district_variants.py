"""Seed the district_name_variants table from the gazetteer JSON.

Usage:
    python scripts/seed_district_variants.py

Requires DATABASE_URL env var or backend/.env file.
Idempotent — uses ON CONFLICT DO NOTHING on (variant_name, source).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
GAZETTEER_FILE = ROOT / "data" / "config" / "gazetteer" / "pakistan_districts.json"

# ── Province lookup ──────────────────────────────────────────────
PROVINCE_BY_PCODE: dict[str, str] = {
    "PK01": "Balochistan",
    "PK02": "Khyber Pakhtunkhwa",
    "PK03": "Sindh",
    "PK04": "Punjab",
    "PK05": "Islamabad Capital Territory",
    "PK06": "Gilgit-Baltistan",
    "PK07": "Azad Jammu & Kashmir",
}

# ── Hand-curated alternative spellings and abbreviations ─────────
# Maps canonical pcode -> list of extra variant strings.
# The gazetteer already contains many aliases (e.g. "dg khan", "ryk"),
# so these are additional ones that may appear in news / police reports.
EXTRA_VARIANTS: dict[str, list[str]] = {
    # Punjab
    "PK0401": ["LHR", "Lhr"],
    "PK0403": ["FSD", "Fsd", "Lyallpur"],
    "PK0404": ["RWP", "Rwp", "Pindi"],
    "PK0406": ["MLT", "Mlt"],
    "PK0411": ["RYK", "R.Y.K.", "R.Y. Khan", "Rahim Yar Khan"],
    "PK0422": ["TTS", "T.T. Singh", "Toba Tek Singh"],
    "PK0417": ["DG Khan", "D.G. Khan", "D.G.Khan", "Dera Ghazi Khan"],
    "PK0427": ["Qasur", "Qasoor"],
    "PK0435": ["Nankana"],
    "PK0409": ["Sheikhupura"],
    "PK0424": ["M.B. Din", "MB Din", "M.B.Din"],
    "PK0434": ["Chiniot"],
    "PK0436": ["Chakwal"],
    "PK0412": ["Gujrat"],
    "PK0402": ["Gujranwala"],

    # Sindh
    "PK0301": ["KHI", "Khi"],
    "PK0308": ["HYD", "Hyd"],
    "PK0311": ["Nawabshah", "Benazirabad", "SBA", "Shaheed Benazirabad"],
    "PK0312": ["Mirpur Khas"],
    "PK0323": ["Naushero Feroze", "N. Feroze", "N.Feroze"],
    "PK0324": ["T. Allahyar", "T.Allahyar"],
    "PK0325": ["TMK", "T.M. Khan", "T.M.Khan"],
    "PK0329": ["Kashmore"],
    "PK0330": ["Qambar", "Shahdadkot"],

    # KP
    "PK0201": ["PSH", "Psh"],
    "PK0205": ["DI Khan", "D.I. Khan", "D.I.Khan", "Dera Ismail Khan"],
    "PK0203": ["Abbotabad", "ATD"],
    "PK0204": ["Mingora"],
    "PK0212": ["Lower Dir"],
    "PK0213": ["Upper Dir"],
    "PK0221": ["Lakki"],
    "PK0224": ["Tor Ghar", "Torghar"],
    "PK0226": ["Lower Chitral"],
    "PK0227": ["NWA", "N. Waziristan", "N.Waziristan"],
    "PK0228": ["SWA", "S. Waziristan", "S.Waziristan"],

    # Balochistan
    "PK0101": ["QTA", "Qta"],
    "PK0124": ["Turbat", "Kech/Turbat"],
    "PK0117": ["Hub"],
    "PK0103": ["Killa Abdullah"],
    "PK0126": ["Killa Saifullah"],
    "PK0110": ["Dera Bugti"],
    "PK0131": ["Jhal Magsi"],

    # ICT
    "PK0501": ["ISB", "Isb", "ICT"],

    # GB
    "PK0601": ["Gilgit"],
    "PK0602": ["Skardu"],

    # AJK
    "PK0701": ["Muzaffarabad"],
    "PK0709": ["Hattian"],
}

SOURCE_TAG = "gazetteer-seed"


# ── Database setup ───────────────────────────────────────────────

def _get_database_url() -> str:
    """Read DATABASE_URL from env or backend/.env file."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env_file = ROOT / "backend" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DATABASE_URL not found in environment or backend/.env")


def _build_engine():
    """Create async SQLAlchemy engine with SSL support for Neon."""
    raw_url = _get_database_url()
    parsed = urlparse(raw_url)
    params = parse_qs(parsed.query)

    needs_ssl = False
    if "sslmode" in params:
        sslmode = params.pop("sslmode")[0]
        needs_ssl = sslmode in ("require", "verify-ca", "verify-full", "prefer")

    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=new_query))

    connect_args: dict = {}
    if needs_ssl:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

    engine = create_async_engine(
        clean_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args=connect_args,
    )
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, session_factory


# ── Variant generation ───────────────────────────────────────────

def _title_case(name: str) -> str:
    """Title-case a district name, preserving dotted abbreviations.

    E.g. "d.g. khan" -> "D.G. Khan", "rahim yar khan" -> "Rahim Yar Khan".
    """
    parts: list[str] = []
    for word in name.split():
        if "." in word:
            # Dotted abbreviation — uppercase each letter segment
            parts.append(".".join(seg.upper() for seg in word.split(".")))
        else:
            parts.append(word.capitalize())
    return " ".join(parts)


def _build_variants_from_gazetteer(
    gazetteer: dict[str, dict],
) -> list[tuple[str, str]]:
    """Generate (variant_name, canonical_pcode) pairs from the gazetteer.

    Only processes district-level entries (admin_level == 3).
    """
    # Group all gazetteer keys by pcode so we can collect aliases
    pcode_to_keys: dict[str, list[str]] = {}
    pcode_to_province: dict[str, str] = {}

    for key, entry in gazetteer.items():
        if entry.get("admin_level") != 3:
            continue
        pcode = entry["pcode"]
        province_pcode = entry.get("province_pcode", "")
        pcode_to_keys.setdefault(pcode, []).append(key)
        if province_pcode and province_pcode not in pcode_to_province:
            pcode_to_province[pcode] = PROVINCE_BY_PCODE.get(province_pcode, "")

    variants: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def _add(variant_name: str, pcode: str) -> None:
        """Add a variant if not already seen (case-insensitive dedup)."""
        key = (variant_name.lower(), pcode)
        if key not in seen:
            seen.add(key)
            variants.append((variant_name, pcode))

    for pcode, keys in pcode_to_keys.items():
        # 1. All gazetteer keys as-is (title-cased) and lowercase
        for raw_key in keys:
            titled = _title_case(raw_key)
            _add(titled, pcode)
            # Also store the raw lowercase form
            _add(raw_key.lower(), pcode)

        # 2. Province-qualified name using the first (canonical) key
        canonical_key = keys[0]
        province_name = pcode_to_province.get(pcode, "")
        if province_name:
            titled = _title_case(canonical_key)
            _add(f"{titled}, {province_name}", pcode)

        # 3. Extra hand-curated variants
        extras = EXTRA_VARIANTS.get(pcode, [])
        for extra in extras:
            _add(extra, pcode)

    return variants


# ── Database insertion ───────────────────────────────────────────

INSERT_SQL = text("""
    INSERT INTO district_name_variants (variant_name, canonical_pcode, source)
    VALUES (:variant_name, :canonical_pcode, :source)
    ON CONFLICT ON CONSTRAINT uq_variant_source DO NOTHING
""")


async def seed(session: AsyncSession, variants: list[tuple[str, str]]) -> int:
    """Insert all variants into district_name_variants. Returns count inserted."""
    inserted = 0
    batch_size = 100

    for i in range(0, len(variants), batch_size):
        batch = variants[i : i + batch_size]
        params = [
            {
                "variant_name": variant_name,
                "canonical_pcode": pcode,
                "source": SOURCE_TAG,
            }
            for variant_name, pcode in batch
        ]
        result = await session.execute(INSERT_SQL, params)
        inserted += result.rowcount  # type: ignore[union-attr]

    await session.commit()
    return inserted


# ── Entrypoint ───────────────────────────────────────────────────

async def main() -> None:
    """Load gazetteer, generate variants, and seed the database."""
    logger.info("Loading gazetteer from %s", GAZETTEER_FILE)
    with open(GAZETTEER_FILE, encoding="utf-8") as f:
        gazetteer = json.load(f)

    logger.info("Loaded %d gazetteer entries", len(gazetteer))

    variants = _build_variants_from_gazetteer(gazetteer)
    logger.info("Generated %d district name variants", len(variants))

    engine, session_factory = _build_engine()

    try:
        async with session_factory() as session:
            # Verify table exists
            check = await session.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name = 'district_name_variants'"
                )
            )
            if check.scalar() == 0:
                logger.error(
                    "Table 'district_name_variants' does not exist. "
                    "Run Alembic migrations first."
                )
                return

            count_before = (
                await session.execute(
                    text("SELECT COUNT(*) FROM district_name_variants")
                )
            ).scalar()

            inserted = await seed(session, variants)
            logger.info(
                "Seeding complete: %d new rows inserted (%d pre-existing, %d total variants generated)",
                inserted,
                count_before,
                len(variants),
            )

            count_after = (
                await session.execute(
                    text("SELECT COUNT(*) FROM district_name_variants")
                )
            ).scalar()
            logger.info("Table now has %d rows", count_after)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
