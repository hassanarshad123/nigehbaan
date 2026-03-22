"""Bootstrap Nigehbaan database with foundation data.

Loads admin boundaries, brick kilns, data source registry, and
initializes vulnerability indicators. Must be run AFTER Alembic
migrations (alembic upgrade head).

Usage:
    DATABASE_URL=postgresql+asyncpg://... python scripts/bootstrap_data.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl
import sys
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
BOUNDARIES_DIR = ROOT / "data" / "raw" / "boundaries"
KILNS_DIR = ROOT / "data" / "raw" / "kilns"
GAZETTEER_FILE = ROOT / "data" / "config" / "gazetteer" / "pakistan_districts.json"

# ── Admin level mapping ──────────────────────────────────────────
# HDX COD-AB uses adm0/1/2/3; our schema uses 1/2/3/4/5.
# HDX has no division level, so we skip admin_level=3.
#   HDX adm0 (country)  -> admin_level=1
#   HDX adm1 (province) -> admin_level=2
#   HDX adm2 (district) -> admin_level=4
#   HDX adm3 (tehsil)   -> admin_level=5

ADMIN_LEVEL_FILES: list[dict] = [
    {
        "file": "pak_admin0.geojson",
        "admin_level": 1,
        "name_key": "adm0_name",
        "pcode_key": "adm0_pcode",
        "parent_pcode_key": None,
    },
    {
        "file": "pak_admin1.geojson",
        "admin_level": 2,
        "name_key": "adm1_name",
        "pcode_key": "adm1_pcode",
        "parent_pcode_key": "adm0_pcode",
    },
    {
        "file": "pak_admin2.geojson",
        "admin_level": 4,
        "name_key": "adm2_name",
        "pcode_key": "adm2_pcode",
        "parent_pcode_key": "adm1_pcode",
    },
    {
        "file": "pak_admin3.geojson",
        "admin_level": 5,
        "name_key": "adm3_name",
        "pcode_key": "adm3_pcode",
        "parent_pcode_key": "adm2_pcode",
    },
]

# ── Data source registry ─────────────────────────────────────────
# Each tuple: (scraper_name, display_name, url, source_type, priority)
# source_type: news, court, police, government, international, ngo, data_loader

DATA_SOURCES: list[tuple[str, str, str, str, int]] = [
    # ── News ──────────────────────────────────────────────────────
    ("rss_monitor", "Google News RSS Monitor", "https://news.google.com/rss/search?q=child+trafficking+Pakistan", "news", 1),
    ("dawn", "Dawn News", "https://www.dawn.com", "news", 1),
    ("tribune", "Express Tribune", "https://tribune.com.pk", "news", 1),
    ("the_news", "The News International", "https://www.thenews.com.pk", "news", 1),
    ("ary_news", "ARY News", "https://arynews.tv", "news", 2),
    ("geo_news", "Geo News", "https://www.geo.tv", "news", 2),
    ("jang_urdu", "Daily Jang (Urdu)", "https://jang.com.pk", "news", 2),
    ("express_urdu", "Express Urdu", "https://www.express.pk", "news", 2),
    ("bbc_urdu", "BBC Urdu", "https://www.bbc.com/urdu", "news", 2),
    ("geo_urdu", "Geo Urdu", "https://urdu.geo.tv", "news", 2),

    # ── Courts ────────────────────────────────────────────────────
    ("scp", "Supreme Court of Pakistan", "https://www.supremecourt.gov.pk", "court", 1),
    ("lhc", "Lahore High Court", "https://www.lhc.gov.pk", "court", 1),
    ("shc", "Sindh High Court", "https://www.sindhhighcourt.gov.pk", "court", 1),
    ("phc", "Peshawar High Court", "https://peshawarhighcourt.gov.pk", "court", 1),
    ("bhc", "Balochistan High Court", "https://bhc.gov.pk", "court", 2),
    ("ihc", "Islamabad High Court", "https://ihc.gov.pk", "court", 2),
    ("commonlii", "CommonLII Pakistan", "https://www.commonlii.org", "court", 2),

    # ── Police ────────────────────────────────────────────────────
    ("police_punjab", "Punjab Police", "https://punjabpolice.gov.pk", "police", 1),
    ("police_sindh", "Sindh Police", "https://sindhpolice.gov.pk", "police", 1),
    ("police_kp", "KP Police", "https://kppolice.gov.pk", "police", 2),
    ("police_balochistan", "Balochistan Police", "https://balochistanpolice.gov.pk", "police", 2),

    # ── Government / NGO ──────────────────────────────────────────
    ("sahil", "Sahil (Cruel Numbers)", "https://sahil.org", "ngo", 1),
    ("stateofchildren", "State of Children", "https://stateofchildren.pk", "government", 2),
    ("pahchaan", "Pahchaan (NADRA)", "https://pahchaan.nadra.gov.pk", "government", 2),
    ("cpwb_punjab", "Punjab CPWB", "https://cpwb.punjab.gov.pk", "government", 1),
    ("ncrc", "National Commission on Rights of Child", "https://ncrc.gov.pk", "government", 2),
    ("roshni_helpline", "Roshni Helpline", "https://roshnihelpline.org", "ngo", 2),
    ("bllf", "Bonded Labour Liberation Front", "https://bllf.org", "ngo", 2),
    ("drf_newsletters", "Digital Rights Foundation", "https://digitalrightsfoundation.pk", "ngo", 2),
    ("bytes_for_all", "Bytes for All", "https://bytesforall.pk", "ngo", 3),
    ("labour_surveys", "Labour Force Surveys (PBS)", "https://www.pbs.gov.pk", "government", 2),
    ("provincial_labour_surveys", "Provincial Labour Surveys", "https://www.pbs.gov.pk", "government", 3),
    ("nchr_organ", "NCHR Organ Trafficking Reports", "https://nchr.gov.pk", "government", 3),
    ("sparc_reports", "SPARC Reports", "https://sparcpk.org", "ngo", 2),
    ("csj_conversion", "CSJ Forced Conversion", "https://csjpak.org", "ngo", 3),
    ("brick_kiln_dashboard", "Brick Kiln Dashboard", "https://brickkilndashboard.org", "government", 2),
    ("kpcpwc", "KP Child Protection & Welfare Commission", "https://kpcpwc.gov.pk", "government", 2),
    ("ssdo_checker", "SSDO (Society for Sustainable Development)", "https://ssdo.org.pk", "ngo", 3),
    ("mohr_checker", "Ministry of Human Rights", "https://mohr.gov.pk", "government", 2),

    # ── Data loaders ──────────────────────────────────────────────
    ("border_crossings", "Border Crossing Points", "https://data.humdata.org", "data_loader", 3),
    ("zenodo_kilns_loader", "Zenodo Brick Kiln Loader", "https://zenodo.org/records/14038648", "data_loader", 2),
    ("walkfree_gsi", "Walk Free Global Slavery Index", "https://www.walkfree.org", "data_loader", 2),
    ("flood_extent", "Flood Extent Data", "https://data.humdata.org", "data_loader", 3),

    # ── International ─────────────────────────────────────────────
    ("tip_report", "US State Dept TIP Report", "https://www.state.gov/trafficking-in-persons-report/", "international", 1),
    ("ctdc", "Counter-Trafficking Data Collaborative", "https://www.ctdatacollaborative.org", "international", 1),
    ("ctdc_dataset", "CTDC Dataset Scraper", "https://www.ctdatacollaborative.org", "international", 2),
    ("unodc", "UNODC Human Trafficking Data", "https://dataunodc.un.org", "international", 1),
    ("worldbank_api", "World Bank API", "https://api.worldbank.org/v2", "international", 2),
    ("unhcr_api", "UNHCR API", "https://api.unhcr.org", "international", 2),
    ("dhs_api", "DHS Program API", "https://api.dhsprogram.com", "international", 2),
    ("ilostat_api", "ILOSTAT API", "https://ilostat.ilo.org/data/", "international", 2),
    ("unicef_pakistan", "UNICEF Pakistan", "https://www.unicef.org/pakistan", "international", 2),
    ("unicef_sdmx", "UNICEF SDMX Data", "https://sdmx.data.unicef.org", "international", 2),
    ("ecpat", "ECPAT International", "https://ecpat.org", "international", 2),
    ("ncmec", "NCMEC Reports", "https://www.missingkids.org", "international", 3),
    ("iwf_reports", "IWF Annual Reports", "https://www.iwf.org.uk", "international", 3),
    ("meta_transparency", "Meta Transparency Reports", "https://transparency.fb.com", "international", 3),
    ("google_transparency", "Google Transparency Reports", "https://transparencyreport.google.com", "international", 3),
    ("weprotect_gta", "WeProtect Global Threat Assessment", "https://www.weprotect.org", "international", 2),
    ("girls_not_brides", "Girls Not Brides", "https://www.girlsnotbrides.org", "international", 2),
    ("corporal_punishment", "End Corporal Punishment", "https://endcorporalpunishment.org", "international", 3),
    ("dol_child_labor", "US DoL Child Labor Data", "https://www.dol.gov/agencies/ilab", "international", 1),
    ("dol_annual_report", "US DoL Annual Report", "https://www.dol.gov/agencies/ilab", "international", 2),
    ("dol_tvpra", "US DoL TVPRA List", "https://www.dol.gov/agencies/ilab", "international", 2),
    ("brookings_bride", "Brookings Child Marriage", "https://www.brookings.edu", "international", 3),
    ("jpp_data", "Justice Project Pakistan", "https://jpp.org.pk", "ngo", 2),
    ("world_prison_brief", "World Prison Brief", "https://www.prisonstudies.org", "international", 3),
    ("zenodo_kilns", "Zenodo Brick Kiln Scraper", "https://zenodo.org/records/14038648", "international", 3),
]


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


# ── Helpers ──────────────────────────────────────────────────────


def _load_geojson(path: Path) -> dict | None:
    """Load and validate a GeoJSON file. Returns None on failure."""
    if not path.exists():
        logger.warning("File not found: %s", path)
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("type") != "FeatureCollection":
            logger.warning("%s is not a FeatureCollection", path.name)
            return None
        features = data.get("features", [])
        if not features:
            logger.warning("%s has zero features", path.name)
            return None
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load %s: %s", path.name, exc)
        return None


def _geometry_to_json(geometry: dict) -> str:
    """Serialize a GeoJSON geometry dict to a JSON string."""
    return json.dumps(geometry, separators=(",", ":"))


# ═════════════════════════════════════════════════════════════════
# STEP 1: Load Admin Boundaries
# ═════════════════════════════════════════════════════════════════


async def load_boundaries(session: AsyncSession) -> int:
    """Load HDX COD-AB admin boundary GeoJSON into the boundaries table.

    Returns total number of boundaries upserted.
    """
    logger.info("=" * 60)
    logger.info("STEP 1: Loading admin boundaries")
    logger.info("=" * 60)

    total = 0

    for level_config in ADMIN_LEVEL_FILES:
        filepath = BOUNDARIES_DIR / level_config["file"]
        admin_level = level_config["admin_level"]
        name_key = level_config["name_key"]
        pcode_key = level_config["pcode_key"]
        parent_pcode_key = level_config["parent_pcode_key"]

        data = _load_geojson(filepath)
        if data is None:
            logger.warning(
                "Skipping admin_level=%d -- file %s not available",
                admin_level,
                level_config["file"],
            )
            continue

        features = data["features"]
        logger.info(
            "Processing %s: %d features (admin_level=%d)",
            level_config["file"],
            len(features),
            admin_level,
        )

        batch_params = []
        for feat in features:
            props = feat.get("properties", {})
            geometry = feat.get("geometry")

            if geometry is None:
                continue

            name_en = props.get(name_key, "Unknown")
            pcode = props.get(pcode_key)
            if not pcode:
                logger.warning("  Feature missing pcode, skipping: %s", name_en)
                continue

            parent_pcode = props.get(parent_pcode_key) if parent_pcode_key else None
            area_sqkm = props.get("area_sqkm")

            # Extract name_ur from alternate language columns if present
            name_ur = props.get(f"{name_key.replace('_name', '_name1')}") or None

            geojson_str = _geometry_to_json(geometry)

            batch_params.append({
                "admin_level": admin_level,
                "name_en": name_en,
                "name_ur": name_ur,
                "pcode": pcode,
                "parent_pcode": parent_pcode,
                "area_sqkm": float(area_sqkm) if area_sqkm is not None else None,
                "geojson_str": geojson_str,
            })

        if not batch_params:
            continue

        # Upsert in batches
        batch_size = 50
        level_count = 0
        for i in range(0, len(batch_params), batch_size):
            batch = batch_params[i : i + batch_size]
            for params in batch:
                await session.execute(
                    text("""
                        INSERT INTO boundaries
                            (admin_level, name_en, name_ur, pcode, parent_pcode, area_sqkm, geometry)
                        VALUES (
                            :admin_level, :name_en, :name_ur, :pcode, :parent_pcode, :area_sqkm,
                            ST_Multi(ST_GeomFromGeoJSON(:geojson_str))
                        )
                        ON CONFLICT (pcode) DO UPDATE SET
                            admin_level = EXCLUDED.admin_level,
                            name_en = EXCLUDED.name_en,
                            name_ur = COALESCE(EXCLUDED.name_ur, boundaries.name_ur),
                            parent_pcode = EXCLUDED.parent_pcode,
                            area_sqkm = COALESCE(EXCLUDED.area_sqkm, boundaries.area_sqkm),
                            geometry = EXCLUDED.geometry
                    """),
                    params,
                )
                level_count += 1

            await session.flush()

        await session.commit()
        total += level_count
        logger.info(
            "  admin_level=%d: %d boundaries upserted", admin_level, level_count
        )

    logger.info("Boundaries total: %d rows upserted", total)
    return total


# ═════════════════════════════════════════════════════════════════
# STEP 2: Load Brick Kilns
# ═════════════════════════════════════════════════════════════════


async def load_brick_kilns(session: AsyncSession) -> int:
    """Load brick kiln GeoJSON data into the brick_kilns table.

    Performs spatial lookup to assign district_pcode.
    Returns count of kilns loaded.
    """
    logger.info("=" * 60)
    logger.info("STEP 2: Loading brick kilns")
    logger.info("=" * 60)

    # Find kiln GeoJSON file
    kiln_files = list(KILNS_DIR.glob("*.geojson"))
    if not kiln_files:
        logger.warning("No kiln GeoJSON files found in %s -- skipping", KILNS_DIR)
        return 0

    kiln_file = kiln_files[0]
    data = _load_geojson(kiln_file)
    if data is None:
        return 0

    features = data["features"]
    logger.info("Processing %s: %d kiln features", kiln_file.name, len(features))

    # Check if brick_kilns table already has data
    existing_count = (
        await session.execute(text("SELECT COUNT(*) FROM brick_kilns"))
    ).scalar() or 0

    if existing_count > 0:
        logger.info(
            "brick_kilns table already has %d rows -- clearing for fresh load",
            existing_count,
        )
        await session.execute(text("DELETE FROM brick_kilns"))
        await session.commit()

    loaded = 0
    batch_size = 200
    skipped = 0

    for i in range(0, len(features), batch_size):
        batch = features[i : i + batch_size]

        for feat in batch:
            geometry = feat.get("geometry")
            props = feat.get("properties", {})

            if geometry is None or geometry.get("type") != "Point":
                skipped += 1
                continue

            coords = geometry.get("coordinates", [])
            if len(coords) < 2:
                skipped += 1
                continue

            lon, lat = coords[0], coords[1]

            # Extract properties from the Zenodo/IGP dataset
            kiln_type = props.get("type")
            nearest_school_m = None
            nearest_hospital_m = None
            population_1km = None

            # The IGP dataset uses "schools1km" (count), "hosp1km" (count), "pop1km"
            schools_1km = props.get("schools1km")
            hosp_1km = props.get("hosp1km")
            pop_1km = props.get("pop1km")

            if pop_1km is not None:
                try:
                    population_1km = int(pop_1km)
                except (ValueError, TypeError):
                    pass

            # Spatial lookup for district_pcode
            district_result = await session.execute(
                text("""
                    SELECT pcode FROM boundaries
                    WHERE admin_level = 4
                      AND ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                    LIMIT 1
                """),
                {"lon": lon, "lat": lat},
            )
            district_row = district_result.fetchone()
            district_pcode = district_row[0] if district_row else None

            await session.execute(
                text("""
                    INSERT INTO brick_kilns
                        (geometry, kiln_type, nearest_school_m, nearest_hospital_m,
                         population_1km, district_pcode, source)
                    VALUES (
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                        :kiln_type, :nearest_school_m, :nearest_hospital_m,
                        :population_1km, :district_pcode, :source
                    )
                """),
                {
                    "lon": lon,
                    "lat": lat,
                    "kiln_type": kiln_type,
                    "nearest_school_m": nearest_school_m,
                    "nearest_hospital_m": nearest_hospital_m,
                    "population_1km": population_1km,
                    "district_pcode": district_pcode,
                    "source": "zenodo-igp-14038648",
                },
            )
            loaded += 1

        await session.flush()

        if (i + batch_size) % 2000 == 0 or (i + batch_size) >= len(features):
            logger.info(
                "  Progress: %d/%d kilns loaded (%d skipped)",
                loaded,
                len(features),
                skipped,
            )

    await session.commit()

    # Count kilns per district for logging
    district_stats = await session.execute(
        text("""
            SELECT district_pcode, COUNT(*) as cnt
            FROM brick_kilns
            WHERE district_pcode IS NOT NULL
            GROUP BY district_pcode
            ORDER BY cnt DESC
            LIMIT 10
        """)
    )
    top_districts = district_stats.fetchall()
    if top_districts:
        logger.info("  Top districts by kiln count:")
        for pcode, cnt in top_districts:
            logger.info("    %s: %d kilns", pcode, cnt)

    unassigned = (
        await session.execute(
            text("SELECT COUNT(*) FROM brick_kilns WHERE district_pcode IS NULL")
        )
    ).scalar() or 0

    logger.info(
        "Brick kilns: %d loaded, %d skipped, %d without district assignment",
        loaded,
        skipped,
        unassigned,
    )
    return loaded


# ═════════════════════════════════════════════════════════════════
# STEP 3: Seed Data Sources
# ═════════════════════════════════════════════════════════════════


async def seed_data_sources(session: AsyncSession) -> int:
    """Insert data source registry entries into the data_sources table.

    Returns count of rows upserted.
    """
    logger.info("=" * 60)
    logger.info("STEP 3: Seeding data source registry")
    logger.info("=" * 60)

    upserted = 0

    for scraper_name, display_name, url, source_type, priority in DATA_SOURCES:
        await session.execute(
            text("""
                INSERT INTO data_sources (name, url, source_type, priority, scraper_name, is_active)
                VALUES (:name, :url, :source_type, :priority, :scraper_name, true)
                ON CONFLICT ON CONSTRAINT data_sources_pkey DO NOTHING
            """),
            {
                "name": display_name,
                "url": url,
                "source_type": source_type,
                "priority": priority,
                "scraper_name": scraper_name,
            },
        )
        upserted += 1

    # data_sources may not have a unique constraint on scraper_name,
    # so try an alternative upsert approach if primary key conflict fails
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.info("  Retrying with scraper_name-based conflict resolution ...")
        for scraper_name, display_name, url, source_type, priority in DATA_SOURCES:
            # Check if this scraper_name already exists
            existing = (
                await session.execute(
                    text("SELECT id FROM data_sources WHERE scraper_name = :sn"),
                    {"sn": scraper_name},
                )
            ).fetchone()

            if existing:
                await session.execute(
                    text("""
                        UPDATE data_sources
                        SET name = :name, url = :url, source_type = :source_type,
                            priority = :priority, is_active = true
                        WHERE scraper_name = :scraper_name
                    """),
                    {
                        "name": display_name,
                        "url": url,
                        "source_type": source_type,
                        "priority": priority,
                        "scraper_name": scraper_name,
                    },
                )
            else:
                await session.execute(
                    text("""
                        INSERT INTO data_sources (name, url, source_type, priority, scraper_name, is_active)
                        VALUES (:name, :url, :source_type, :priority, :scraper_name, true)
                    """),
                    {
                        "name": display_name,
                        "url": url,
                        "source_type": source_type,
                        "priority": priority,
                        "scraper_name": scraper_name,
                    },
                )
        await session.commit()

    logger.info("Data sources: %d entries upserted", upserted)
    return upserted


# ═════════════════════════════════════════════════════════════════
# STEP 4: Seed District Name Variants
# ═════════════════════════════════════════════════════════════════


async def seed_district_variants(session: AsyncSession) -> int:
    """Load district name variants from the gazetteer.

    Delegates to the logic in seed_district_variants.py but inlined
    here for self-contained execution.

    Returns count of variants inserted.
    """
    logger.info("=" * 60)
    logger.info("STEP 4: Seeding district name variants")
    logger.info("=" * 60)

    # Check table exists
    table_check = await session.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'district_name_variants'"
        )
    )
    if table_check.scalar() == 0:
        logger.warning("Table 'district_name_variants' does not exist -- skipping")
        return 0

    if not GAZETTEER_FILE.exists():
        logger.warning("Gazetteer file not found: %s -- skipping", GAZETTEER_FILE)
        return 0

    with open(GAZETTEER_FILE, encoding="utf-8") as f:
        gazetteer = json.load(f)

    logger.info("  Loaded %d gazetteer entries", len(gazetteer))

    # Province lookup for qualified names
    province_by_pcode: dict[str, str] = {
        "PK01": "Balochistan",
        "PK02": "Khyber Pakhtunkhwa",
        "PK03": "Sindh",
        "PK04": "Punjab",
        "PK05": "Islamabad Capital Territory",
        "PK06": "Gilgit-Baltistan",
        "PK07": "Azad Jammu & Kashmir",
    }

    # Group gazetteer keys by pcode
    pcode_to_keys: dict[str, list[str]] = {}
    pcode_to_province: dict[str, str] = {}

    for key, entry in gazetteer.items():
        if entry.get("admin_level") != 3:
            continue
        pcode = entry["pcode"]
        province_pcode = entry.get("province_pcode", "")
        pcode_to_keys.setdefault(pcode, []).append(key)
        if province_pcode:
            pcode_to_province[pcode] = province_by_pcode.get(province_pcode, "")

    # Generate variants
    variants: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def _add(variant_name: str, pcode: str) -> None:
        key = (variant_name.lower(), pcode)
        if key not in seen:
            seen.add(key)
            variants.append((variant_name, pcode))

    def _title_case(name: str) -> str:
        parts: list[str] = []
        for word in name.split():
            if "." in word:
                parts.append(".".join(seg.upper() for seg in word.split(".")))
            else:
                parts.append(word.capitalize())
        return " ".join(parts)

    for pcode, keys in pcode_to_keys.items():
        for raw_key in keys:
            titled = _title_case(raw_key)
            _add(titled, pcode)
            _add(raw_key.lower(), pcode)

        canonical_key = keys[0]
        province_name = pcode_to_province.get(pcode, "")
        if province_name:
            titled = _title_case(canonical_key)
            _add(f"{titled}, {province_name}", pcode)

    logger.info("  Generated %d variants", len(variants))

    # Insert in batches
    inserted = 0
    batch_size = 100
    source_tag = "gazetteer-seed"

    for i in range(0, len(variants), batch_size):
        batch = variants[i : i + batch_size]
        for variant_name, pcode in batch:
            result = await session.execute(
                text("""
                    INSERT INTO district_name_variants (variant_name, canonical_pcode, source)
                    VALUES (:variant_name, :canonical_pcode, :source)
                    ON CONFLICT ON CONSTRAINT uq_variant_source DO NOTHING
                """),
                {
                    "variant_name": variant_name,
                    "canonical_pcode": pcode,
                    "source": source_tag,
                },
            )
            inserted += result.rowcount

    await session.commit()
    logger.info("District name variants: %d new rows inserted", inserted)
    return inserted


# ═════════════════════════════════════════════════════════════════
# STEP 5: Initialize Vulnerability Indicators
# ═════════════════════════════════════════════════════════════════


async def init_vulnerability_indicators(session: AsyncSession) -> int:
    """Create baseline vulnerability_indicators rows for each district.

    Sets year=2024, trafficking_risk_score=0, all other indicators NULL.
    These get populated when scrapers run and weekly risk_scores task executes.

    Returns count of rows created.
    """
    logger.info("=" * 60)
    logger.info("STEP 5: Initializing vulnerability indicators")
    logger.info("=" * 60)

    # Check table exists
    table_check = await session.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'vulnerability_indicators'"
        )
    )
    if table_check.scalar() == 0:
        logger.warning("Table 'vulnerability_indicators' does not exist -- skipping")
        return 0

    # Get all district pcodes
    districts = await session.execute(
        text("SELECT pcode FROM boundaries WHERE admin_level = 4 ORDER BY pcode")
    )
    district_pcodes = [row[0] for row in districts.fetchall()]

    if not district_pcodes:
        logger.warning("No districts found in boundaries table -- skipping")
        return 0

    logger.info("  Found %d districts for vulnerability baseline", len(district_pcodes))

    created = 0
    for pcode in district_pcodes:
        result = await session.execute(
            text("""
                INSERT INTO vulnerability_indicators (district_pcode, year, trafficking_risk_score, source)
                VALUES (:district_pcode, :year, :risk_score, :source)
                ON CONFLICT ON CONSTRAINT uq_vuln_district_year DO NOTHING
            """),
            {
                "district_pcode": pcode,
                "year": 2024,
                "risk_score": 0.0,
                "source": "bootstrap-baseline",
            },
        )
        created += result.rowcount

    await session.commit()
    logger.info("Vulnerability indicators: %d baseline rows created", created)
    return created


# ═════════════════════════════════════════════════════════════════
# Main orchestrator
# ═════════════════════════════════════════════════════════════════


async def main() -> int:
    """Run all bootstrap steps in order. Returns 0 on success."""
    logger.info("")
    logger.info("*" * 60)
    logger.info("  Nigehbaan Database Bootstrap")
    logger.info("*" * 60)
    logger.info("")

    engine, session_factory = _build_engine()
    results: dict[str, int] = {}
    errors: list[str] = []

    try:
        async with session_factory() as session:
            # Verify PostGIS is available
            try:
                postgis_check = await session.execute(
                    text("SELECT PostGIS_Version()")
                )
                version = postgis_check.scalar()
                logger.info("PostGIS version: %s", version)
            except Exception:
                logger.error(
                    "PostGIS extension not found. Run: CREATE EXTENSION postgis;"
                )
                return 1

            # Verify boundaries table exists
            table_check = await session.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name = 'boundaries'"
                )
            )
            if table_check.scalar() == 0:
                logger.error(
                    "Table 'boundaries' does not exist. "
                    "Run Alembic migrations first: alembic upgrade head"
                )
                return 1

            # Step 1: Boundaries (must be first -- other steps depend on it)
            try:
                results["boundaries"] = await load_boundaries(session)
            except Exception as exc:
                logger.error("STEP 1 FAILED: %s", exc, exc_info=True)
                errors.append(f"boundaries: {exc}")

            # Step 2: Brick Kilns (depends on boundaries for spatial join)
            try:
                results["brick_kilns"] = await load_brick_kilns(session)
            except Exception as exc:
                logger.error("STEP 2 FAILED: %s", exc, exc_info=True)
                errors.append(f"brick_kilns: {exc}")

            # Step 3: Data Sources
            try:
                results["data_sources"] = await seed_data_sources(session)
            except Exception as exc:
                logger.error("STEP 3 FAILED: %s", exc, exc_info=True)
                errors.append(f"data_sources: {exc}")

            # Step 4: District Name Variants
            try:
                results["district_variants"] = await seed_district_variants(session)
            except Exception as exc:
                logger.error("STEP 4 FAILED: %s", exc, exc_info=True)
                errors.append(f"district_variants: {exc}")

            # Step 5: Vulnerability Indicators (depends on boundaries)
            try:
                results["vulnerability"] = await init_vulnerability_indicators(session)
            except Exception as exc:
                logger.error("STEP 5 FAILED: %s", exc, exc_info=True)
                errors.append(f"vulnerability: {exc}")

    finally:
        await engine.dispose()

    # ── Summary ──────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("  BOOTSTRAP SUMMARY")
    logger.info("=" * 60)
    for step_name, count in results.items():
        logger.info("  %-25s %d rows", step_name, count)
    if errors:
        logger.warning("")
        logger.warning("  ERRORS (%d):", len(errors))
        for err in errors:
            logger.warning("    - %s", err)
    else:
        logger.info("")
        logger.info("  All steps completed successfully.")
    logger.info("=" * 60)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
