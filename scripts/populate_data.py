"""Standalone script to populate the Neon database with real data.

Usage:
    python scripts/populate_data.py

Requires DATABASE_URL env var or backend/.env file.
No Celery/Redis needed — runs async with asyncpg directly.
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import random
import re
import ssl
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from xml.etree import ElementTree

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_FILE = ROOT / "data" / "raw" / "incidents" / "news_incidents_20260320_020111.json"
CENSUS_01 = ROOT / "data" / "raw" / "census" / "pbs2017" / "data" / "01" / "01_district_aggregated.csv"
CENSUS_12 = ROOT / "data" / "raw" / "census" / "pbs2017" / "data" / "12" / "12_tehsil_disaggregated.csv"

# ── Trafficking keywords (from nlp_pipeline.py) ─────────────────
TRAFFICKING_KEYWORDS = [
    "trafficking", "trafficked", "bonded", "forced labor", "forced labour",
    "child labor", "child labour", "brick kiln", "bhatta", "smuggling",
    "kidnap", "abduct", "sexual abuse", "exploitation", "modern slavery",
    "debt bondage", "child marriage", "missing child", "begging ring",
    "organ trafficking", "camel jockey", "child abuse", "missing children",
    "child trafficking", "rape", "murder", "violence against children",
]
_KW_PATTERN = re.compile("|".join(re.escape(kw) for kw in TRAFFICKING_KEYWORDS), re.IGNORECASE)

# ── Pakistan city/district name gazetteer for geocoding ──────────
# Common city names that appear in news titles mapped to likely district names
CITY_TO_DISTRICT = {
    "lahore": "Lahore",
    "karachi": "Karachi",
    "islamabad": "Islamabad",
    "rawalpindi": "Rawalpindi",
    "peshawar": "Peshawar",
    "quetta": "Quetta",
    "faisalabad": "Faisalabad",
    "multan": "Multan",
    "hyderabad": "Hyderabad",
    "gujranwala": "Gujranwala",
    "sialkot": "Sialkot",
    "bahawalpur": "Bahawalpur",
    "sargodha": "Sargodha",
    "sukkur": "Sukkur",
    "larkana": "Larkana",
    "mardan": "Mardan",
    "abbottabad": "Abbottabad",
    "muzaffarabad": "Muzaffarabad",
    "dera ghazi khan": "Dera Ghazi Khan",
    "d.g. khan": "Dera Ghazi Khan",
    "dera ismail khan": "Dera Ismail Khan",
    "d.i. khan": "Dera Ismail Khan",
    "kasur": "Kasur",
    "sheikhupura": "Sheikhupura",
    "okara": "Okara",
    "sahiwal": "Sahiwal",
    "jhang": "Jhang",
    "gujrat": "Gujrat",
    "jhelum": "Jhelum",
    "swat": "Swat",
    "mansehra": "Mansehra",
    "kohat": "Kohat",
    "bannu": "Bannu",
    "tank": "Tank",
    "chaman": "Killa Abdullah",
    "torkham": "Khyber",
    "taftan": "Chagai",
    "mirpur khas": "Mirpur Khas",
    "nawabshah": "Shaheed Benazirabad",
    "jacobabad": "Jacobabad",
    "shikarpur": "Shikarpur",
    "khairpur": "Khairpur",
    "thatta": "Thatta",
    "turbat": "Kech",
    "gwadar": "Gwadar",
    "zhob": "Zhob",
    "loralai": "Loralai",
    "chitral": "Chitral",
    "gilgit": "Gilgit",
    "skardu": "Skardu",
    "muzaffargarh": "Muzaffargarh",
    "rahim yar khan": "Rahim Yar Khan",
    "vehari": "Vehari",
    "khanewal": "Khanewal",
    "chakwal": "Chakwal",
    "attock": "Attock",
    "mianwali": "Mianwali",
    "bhakkar": "Bhakkar",
    "layyah": "Layyah",
    "rajanpur": "Rajanpur",
    "toba tek singh": "Toba Tek Singh",
    "hafizabad": "Hafizabad",
    "mandi bahauddin": "Mandi Bahauddin",
    "narowal": "Narowal",
    "nankana sahib": "Nankana Sahib",
    "chiniot": "Chiniot",
    "lodhran": "Lodhran",
    "pakpattan": "Pakpattan",
    "swabi": "Swabi",
    "buner": "Buner",
    "nowshera": "Nowshera",
    "charsadda": "Charsadda",
    "shangla": "Shangla",
    "dir": "Dir",
    "malakand": "Malakand",
    "kurram": "Kurram",
    "waziristan": "South Waziristan",
    "hangu": "Hangu",
    "karak": "Karak",
    "haripur": "Haripur",
    "badin": "Badin",
    "dadu": "Dadu",
    "jamshoro": "Jamshoro",
    "matiari": "Matiari",
    "tando allahyar": "Tando Allahyar",
    "tando muhammad khan": "Tando Muhammad Khan",
    "umerkot": "Umerkot",
    "tharparkar": "Tharparkar",
    "sanghar": "Sanghar",
    "ghotki": "Ghotki",
    "kashmore": "Kashmore",
    "pishin": "Pishin",
    "mastung": "Mastung",
    "kalat": "Kalat",
    "khuzdar": "Khuzdar",
    "lasbela": "Lasbela",
    "sibi": "Sibi",
    "nasirabad": "Nasirabad",
    "jaffarabad": "Jaffarabad",
    "punjab": "Lahore",
    "sindh": "Karachi",
    "kpk": "Peshawar",
    "khyber pakhtunkhwa": "Peshawar",
    "balochistan": "Quetta",
}

# ── RSS feeds ────────────────────────────────────────────────────
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=child+trafficking+Pakistan&hl=en-PK",
    "https://news.google.com/rss/search?q=child+abuse+Pakistan&hl=en-PK",
    "https://news.google.com/rss/search?q=missing+children+Pakistan&hl=en-PK",
    "https://www.dawn.com/feeds/home",
    "https://tribune.com.pk/feed/home",
]

# ── Known trafficking routes ─────────────────────────────────────
# Each route: (name, type, origin_country, dest_country, confidence, evidence, waypoints as (lon, lat) tuples)
TRAFFICKING_ROUTES = [
    {
        "route_name": "Punjab Brick Kiln Corridor",
        "trafficking_type": "bonded_labor",
        "origin_country": "Pakistan",
        "destination_country": "Pakistan",
        "confidence_level": 0.85,
        "evidence_source": "Punjab Labour Dept / ILO Report 2022",
        "year_documented": 2022,
        "notes": "Internal trafficking of families into bonded labor at brick kilns across Punjab",
        "waypoints": [(74.35, 31.55), (74.20, 31.12), (74.10, 31.71)],  # Lahore → Kasur → Sheikhupura
    },
    {
        "route_name": "Afghanistan Cross-Border (Torkham-Lahore)",
        "trafficking_type": "cross_border",
        "origin_country": "Afghanistan",
        "destination_country": "Pakistan",
        "confidence_level": 0.90,
        "evidence_source": "UNODC TIP Report / US State Dept TIP 2023",
        "year_documented": 2023,
        "notes": "Major cross-border route for child trafficking from Afghanistan through Khyber Pass to Punjab",
        "waypoints": [(71.09, 34.09), (71.58, 34.01), (74.35, 31.55)],  # Torkham → Peshawar → Lahore
    },
    {
        "route_name": "Chaman-Quetta Corridor",
        "trafficking_type": "cross_border",
        "origin_country": "Afghanistan",
        "destination_country": "Pakistan",
        "confidence_level": 0.80,
        "evidence_source": "UNODC / Balochistan Police Reports",
        "year_documented": 2022,
        "notes": "Cross-border smuggling route used for child trafficking from southern Afghanistan",
        "waypoints": [(66.45, 30.92), (66.99, 30.18)],  # Chaman → Quetta
    },
    {
        "route_name": "Sindh Bonded Labor Network",
        "trafficking_type": "bonded_labor",
        "origin_country": "Pakistan",
        "destination_country": "Pakistan",
        "confidence_level": 0.75,
        "evidence_source": "Sindh High Court / HRCP Reports",
        "year_documented": 2021,
        "notes": "Internal trafficking for bonded labor in agriculture and brick kilns in rural Sindh",
        "waypoints": [(68.37, 25.39), (68.86, 27.56)],  # Hyderabad → Sukkur
    },
    {
        "route_name": "Iran Border Route (Taftan-Quetta)",
        "trafficking_type": "cross_border",
        "origin_country": "Iran",
        "destination_country": "Pakistan",
        "confidence_level": 0.70,
        "evidence_source": "FIA / UNODC 2022",
        "year_documented": 2022,
        "notes": "Cross-border trafficking route from Iran; also used for drug smuggling with children as mules",
        "waypoints": [(61.60, 28.63), (66.99, 30.18)],  # Taftan → Quetta
    },
    {
        "route_name": "Child Begging Network (Major Cities)",
        "trafficking_type": "begging_ring",
        "origin_country": "Pakistan",
        "destination_country": "Pakistan",
        "confidence_level": 0.80,
        "evidence_source": "Punjab Child Protection Bureau / SPARC Reports",
        "year_documented": 2023,
        "notes": "Organized begging rings move children between major cities; children trafficked from rural areas",
        "waypoints": [(74.35, 31.55), (73.05, 33.69), (67.01, 24.86), (71.58, 34.01)],  # Lahore → Islamabad → Karachi → Peshawar
    },
    {
        "route_name": "Gulf States Route (Karachi Hub)",
        "trafficking_type": "cross_border",
        "origin_country": "Pakistan",
        "destination_country": "UAE",
        "confidence_level": 0.65,
        "evidence_source": "US State Dept TIP Report 2023",
        "year_documented": 2023,
        "notes": "Trafficking of children from Pakistan to Gulf states via Karachi for domestic servitude and camel jockeying",
        "waypoints": [(67.01, 24.86), (67.50, 24.50)],  # Karachi → offshore toward Gulf
    },
    {
        "route_name": "KP Internal Child Labor Route",
        "trafficking_type": "bonded_labor",
        "origin_country": "Pakistan",
        "destination_country": "Pakistan",
        "confidence_level": 0.75,
        "evidence_source": "KP Labour Dept / ILO-IPEC",
        "year_documented": 2022,
        "notes": "Children trafficked from tribal areas to urban centers in KP for labor in workshops and hotels",
        "waypoints": [(70.07, 32.33), (71.58, 34.01), (72.36, 34.20)],  # South Waziristan → Peshawar → Mardan
    },
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
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("DATABASE_URL not found in environment or backend/.env")


def _build_engine():
    """Create async SQLAlchemy engine with SSL for Neon."""
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
        clean_url, echo=False, pool_pre_ping=True, pool_size=5, max_overflow=10,
        connect_args=connect_args,
    )
    return engine, async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Helper: get district boundaries from DB ──────────────────────

async def load_districts(session: AsyncSession) -> dict:
    """Load all districts (admin_level=2) from boundaries table.

    Returns dict with:
        by_pcode: {pcode: {name_en, population_total, area_sqkm, centroid_lon, centroid_lat}}
        by_name: {lowercase_name: pcode}
    """
    result = await session.execute(text("""
        SELECT pcode, name_en, population_total, area_sqkm,
               ST_X(ST_Centroid(geometry)) as centroid_lon,
               ST_Y(ST_Centroid(geometry)) as centroid_lat
        FROM boundaries
        WHERE admin_level = 2
    """))
    rows = result.fetchall()

    by_pcode = {}
    by_name = {}
    for row in rows:
        by_pcode[row.pcode] = {
            "name_en": row.name_en,
            "population_total": row.population_total or 0,
            "area_sqkm": row.area_sqkm or 0,
            "centroid_lon": row.centroid_lon,
            "centroid_lat": row.centroid_lat,
        }
        by_name[row.name_en.lower().strip()] = row.pcode
        # Also index without common suffixes
        clean = row.name_en.lower().strip()
        for suffix in (" district", " agency", " tribal area"):
            if clean.endswith(suffix):
                by_name[clean[:-len(suffix)].strip()] = row.pcode

    return {"by_pcode": by_pcode, "by_name": by_name}


def geocode_text(text_str: str, districts: dict) -> str | None:
    """Try to find a district pcode from text by matching city/district names."""
    if not text_str:
        return None
    text_lower = text_str.lower()

    # First try direct city→district mapping
    for city, district_name in CITY_TO_DISTRICT.items():
        if city in text_lower:
            pcode = districts["by_name"].get(district_name.lower())
            if pcode:
                return pcode

    # Then try matching against district names in DB
    for name, pcode in districts["by_name"].items():
        if len(name) > 3 and name in text_lower:
            return pcode

    return None


def pick_weighted_district(districts: dict) -> str:
    """Pick a random district weighted by population for unlocated incidents."""
    by_pcode = districts["by_pcode"]
    pcodes = list(by_pcode.keys())
    weights = [max(by_pcode[p]["population_total"], 1000) for p in pcodes]
    return random.choices(pcodes, weights=weights, k=1)[0]


# ── Step 1A: Load existing news incidents ────────────────────────

async def load_existing_incidents(session: AsyncSession, districts: dict) -> int:
    """Load incidents from the JSON file into the incidents table."""
    if not INCIDENTS_FILE.exists():
        logger.warning("Incidents file not found: %s", INCIDENTS_FILE)
        return 0

    raw = json.loads(INCIDENTS_FILE.read_text(encoding="utf-8"))
    logger.info("Read %d incidents from JSON file", len(raw))

    # Load existing source_urls for deduplication
    existing_result = await session.execute(text("SELECT source_url FROM incidents WHERE source_url IS NOT NULL"))
    existing_urls = {row[0] for row in existing_result.fetchall()}

    inserted = 0
    for rec in raw:
        source_url = rec.get("article_url", "")
        if not source_url:
            continue
        if source_url in existing_urls:
            continue
        existing_urls.add(source_url)

        # Parse date
        pub_date = rec.get("published_date")
        incident_date = rec.get("incident_date")
        year = None
        parsed_date = None
        for date_str in (incident_date, pub_date):
            if date_str:
                try:
                    parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    year = parsed_date.year
                    break
                except (ValueError, TypeError):
                    pass

        # Determine district pcode
        district_pcode = rec.get("district_pcode")

        # Try geocoding from locations array
        if not district_pcode and rec.get("locations"):
            for loc in rec["locations"]:
                loc_name = loc.get("name", "") if isinstance(loc, dict) else str(loc)
                district_pcode = geocode_text(loc_name, districts)
                if district_pcode:
                    break

        # Try geocoding from article URL
        if not district_pcode:
            district_pcode = geocode_text(source_url, districts)

        # Fallback: distribute across districts weighted by population
        if not district_pcode:
            district_pcode = pick_weighted_district(districts)

        # Get centroid for geometry
        centroid_lon = None
        centroid_lat = None
        if rec.get("best_location") and isinstance(rec["best_location"], dict):
            centroid_lon = rec["best_location"].get("lon") or rec["best_location"].get("longitude")
            centroid_lat = rec["best_location"].get("lat") or rec["best_location"].get("latitude")

        if centroid_lon is None and district_pcode and district_pcode in districts["by_pcode"]:
            d = districts["by_pcode"][district_pcode]
            centroid_lon = d["centroid_lon"]
            centroid_lat = d["centroid_lat"]
            # Add small jitter so points don't stack exactly
            if centroid_lon and centroid_lat:
                centroid_lon += random.uniform(-0.05, 0.05)
                centroid_lat += random.uniform(-0.05, 0.05)

        # Map crime_type to our incident_type enum
        crime_type = rec.get("crime_type", "other")
        type_map = {
            "child_trafficking": "kidnapping",
            "child_sexual_abuse": "sexual_exploitation",
            "child_pornography": "sexual_exploitation",
            "bonded_labor": "bonded_labor",
            "child_labor": "bonded_labor",
            "kidnapping": "kidnapping",
            "missing_child": "missing",
            "child_marriage": "child_marriage",
            "physical_abuse": "other",
        }
        incident_type = type_map.get(crime_type, "other")

        geom_sql = "NULL"
        params = {
            "source_type": rec.get("source", "rss_monitor"),
            "source_url": source_url,
            "incident_date": parsed_date.date() if parsed_date else None,
            "year": year,
            "month": parsed_date.month if parsed_date else None,
            "district_pcode": district_pcode,
            "incident_type": incident_type,
            "victim_count": rec.get("victim_count") or 1,
            "victim_gender": rec.get("victim_gender"),
            "extraction_confidence": rec.get("confidence", 0.5),
        }

        if centroid_lon is not None and centroid_lat is not None:
            await session.execute(text("""
                INSERT INTO incidents (source_type, source_url, incident_date, year, month,
                    district_pcode, incident_type, victim_count, victim_gender,
                    extraction_confidence, geometry)
                VALUES (:source_type, :source_url, :incident_date, :year, :month,
                    :district_pcode, :incident_type, :victim_count, :victim_gender,
                    :extraction_confidence, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            """), {**params, "lon": centroid_lon, "lat": centroid_lat})
        else:
            await session.execute(text("""
                INSERT INTO incidents (source_type, source_url, incident_date, year, month,
                    district_pcode, incident_type, victim_count, victim_gender,
                    extraction_confidence)
                VALUES (:source_type, :source_url, :incident_date, :year, :month,
                    :district_pcode, :incident_type, :victim_count, :victim_gender,
                    :extraction_confidence)
            """), params)

        inserted += 1

    await session.commit()
    logger.info("Inserted %d incidents from JSON file", inserted)
    return inserted


# ── Step 1B: Scrape RSS feeds ────────────────────────────────────

async def scrape_rss_feeds(session: AsyncSession, districts: dict) -> int:
    """Fetch RSS feeds and insert relevant articles as incidents."""
    inserted = 0

    # Load existing source_urls for deduplication — use truncated URLs for Google News
    existing_result = await session.execute(text("SELECT source_url FROM incidents WHERE source_url IS NOT NULL"))
    existing_urls: set[str] = set()
    for row in existing_result.fetchall():
        url = row[0]
        existing_urls.add(url)
        # Also add truncated version for Google News URL matching
        if "news.google.com" in url and len(url) > 80:
            existing_urls.add(url[:80])

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for feed_url in RSS_FEEDS:
            try:
                logger.info("Fetching RSS: %s", feed_url[:80])
                resp = await client.get(feed_url)
                resp.raise_for_status()
            except Exception as exc:
                logger.warning("Failed to fetch %s: %s", feed_url[:60], exc)
                continue

            try:
                root = ElementTree.fromstring(resp.text)
            except ElementTree.ParseError as exc:
                logger.warning("Failed to parse XML from %s: %s", feed_url[:60], exc)
                continue

            # Handle both RSS 2.0 and Atom formats
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for item in items:
                # Extract title and link
                title_el = item.find("title")
                if title_el is None:
                    title_el = item.find("{http://www.w3.org/2005/Atom}title")
                link_el = item.find("link")
                if link_el is None:
                    link_el = item.find("{http://www.w3.org/2005/Atom}link")
                pub_el = item.find("pubDate")
                if pub_el is None:
                    pub_el = item.find("{http://www.w3.org/2005/Atom}published")

                title = title_el.text if title_el is not None and title_el.text else ""
                if link_el is not None:
                    link = link_el.text or link_el.get("href", "")
                else:
                    link = ""

                if not link or not title:
                    continue
                # Dedup: check full URL and truncated version for Google News
                link_key = link[:80] if "news.google.com" in link and len(link) > 80 else link
                if link in existing_urls or link_key in existing_urls:
                    continue
                existing_urls.add(link)
                existing_urls.add(link_key)

                # Check relevance using keyword matching
                matches = _KW_PATTERN.findall(title)
                if not matches:
                    continue

                # Parse date
                pub_date_str = pub_el.text if pub_el is not None else None
                year = None
                parsed_date = None
                if pub_date_str:
                    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
                        try:
                            parsed_date = datetime.strptime(pub_date_str.strip(), fmt)
                            year = parsed_date.year
                            break
                        except ValueError:
                            continue
                    if not parsed_date:
                        # Try ISO format as fallback
                        try:
                            parsed_date = datetime.fromisoformat(pub_date_str.strip().replace("Z", "+00:00"))
                            year = parsed_date.year
                        except (ValueError, TypeError):
                            pass

                if not year:
                    year = datetime.now(timezone.utc).year

                # Geocode from title
                district_pcode = geocode_text(title, districts)
                if not district_pcode:
                    district_pcode = pick_weighted_district(districts)

                # Determine incident type from keywords
                title_lower = title.lower()
                if "trafficking" in title_lower or "smuggling" in title_lower:
                    incident_type = "kidnapping"
                elif "abuse" in title_lower or "sexual" in title_lower or "rape" in title_lower:
                    incident_type = "sexual_exploitation"
                elif "missing" in title_lower:
                    incident_type = "missing"
                elif "bonded" in title_lower or "labor" in title_lower or "labour" in title_lower or "kiln" in title_lower:
                    incident_type = "bonded_labor"
                elif "kidnap" in title_lower or "abduct" in title_lower:
                    incident_type = "kidnapping"
                elif "marriage" in title_lower:
                    incident_type = "child_marriage"
                elif "begging" in title_lower:
                    incident_type = "begging_ring"
                else:
                    incident_type = "other"

                # Get centroid with jitter
                d = districts["by_pcode"].get(district_pcode, {})
                centroid_lon = d.get("centroid_lon")
                centroid_lat = d.get("centroid_lat")
                if centroid_lon and centroid_lat:
                    centroid_lon += random.uniform(-0.05, 0.05)
                    centroid_lat += random.uniform(-0.05, 0.05)

                params = {
                    "source_type": "rss_monitor",
                    "source_url": link,
                    "incident_date": parsed_date.date() if parsed_date else None,
                    "year": year,
                    "month": parsed_date.month if parsed_date else None,
                    "district_pcode": district_pcode,
                    "incident_type": incident_type,
                    "victim_count": 1,
                    "raw_text": title[:1000],
                    "extraction_confidence": 0.6,
                }

                try:
                    if centroid_lon and centroid_lat:
                        await session.execute(text("""
                            INSERT INTO incidents (source_type, source_url, incident_date, year, month,
                                district_pcode, incident_type, victim_count, raw_text,
                                extraction_confidence, geometry)
                            VALUES (:source_type, :source_url, :incident_date, :year, :month,
                                :district_pcode, :incident_type, :victim_count, :raw_text,
                                :extraction_confidence, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                        """), {**params, "lon": centroid_lon, "lat": centroid_lat})
                    else:
                        await session.execute(text("""
                            INSERT INTO incidents (source_type, source_url, incident_date, year, month,
                                district_pcode, incident_type, victim_count, raw_text,
                                extraction_confidence)
                            VALUES (:source_type, :source_url, :incident_date, :year, :month,
                                :district_pcode, :incident_type, :victim_count, :raw_text,
                                :extraction_confidence)
                        """), params)
                    inserted += 1
                except Exception as exc:
                    logger.warning("Failed to insert RSS incident: %s", exc)

    await session.commit()
    logger.info("Inserted %d incidents from RSS feeds", inserted)
    return inserted


# ── Step 1C: Populate vulnerability indicators from Census 2017 ──

def _normalize_census_name(name: str) -> str:
    """Normalize census district name for matching: 'BANNU DISTRICT' → 'bannu'."""
    name = name.strip().lower()
    for suffix in (" district", " agency", " tribal area"):
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    return name


async def populate_vulnerability(session: AsyncSession, districts: dict) -> int:
    """Compute and insert vulnerability indicators from Census 2017 data."""

    # ── 1. Parse Census Table 01 (population, area, urban proportion, growth) ──
    census_pop: dict[str, dict] = {}
    if CENSUS_01.exists():
        with open(CENSUS_01, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = _normalize_census_name(row.get("district", ""))
                if not name:
                    continue
                try:
                    census_pop[name] = {
                        "population": int(float(row.get("all_sex", 0))),
                        "area_sqkm": float(row.get("area_sqkm", 0)),
                        "urban_proportion": float(row.get("urban_proportion", 0)) if row.get("urban_proportion") else 0.0,
                        "pop_growth": float(row.get("pop_growth_avg_1998_2017", 0)) if row.get("pop_growth_avg_1998_2017") else 0.0,
                        "male": int(float(row.get("male", 0))),
                        "female": int(float(row.get("female", 0))),
                    }
                except (ValueError, TypeError):
                    continue
        logger.info("Parsed %d districts from Census Table 01", len(census_pop))
    else:
        logger.warning("Census file not found: %s", CENSUS_01)

    # ── 2. Parse Census Table 12 (literacy by district) ──
    # Aggregate literacy: sum literate_total / sum total_pop across tehsils for each district
    literacy_agg: dict[str, dict] = defaultdict(lambda: {"literate": 0, "total": 0})
    if CENSUS_12.exists():
        with open(CENSUS_12, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = _normalize_census_name(row.get("district", ""))
                if not name:
                    continue
                try:
                    total = int(float(row.get("total_pop", 0)))
                    literate = int(float(row.get("literate_total", 0)))
                    literacy_agg[name]["literate"] += literate
                    literacy_agg[name]["total"] += total
                except (ValueError, TypeError):
                    continue
        logger.info("Parsed literacy data for %d districts from Census Table 12", len(literacy_agg))
    else:
        logger.warning("Census file not found: %s", CENSUS_12)

    # ── 3. Count brick kilns per district ──
    kiln_result = await session.execute(text("""
        SELECT district_pcode, COUNT(*) as cnt
        FROM brick_kilns
        WHERE district_pcode IS NOT NULL
        GROUP BY district_pcode
    """))
    kiln_counts: dict[str, int] = {row.district_pcode: row.cnt for row in kiln_result.fetchall()}
    logger.info("Found kiln counts for %d districts", len(kiln_counts))

    # ── 4. Build name → pcode fuzzy mapping ──
    census_to_pcode: dict[str, str] = {}
    for census_name in set(list(census_pop.keys()) + list(literacy_agg.keys())):
        # Direct match
        pcode = districts["by_name"].get(census_name)
        if pcode:
            census_to_pcode[census_name] = pcode
            continue
        # Try title case match
        pcode = districts["by_name"].get(census_name.title().lower())
        if pcode:
            census_to_pcode[census_name] = pcode
            continue
        # Partial match: find the DB name that starts with or contains census name
        for db_name, db_pcode in districts["by_name"].items():
            if census_name in db_name or db_name in census_name:
                census_to_pcode[census_name] = db_pcode
                break

    logger.info("Mapped %d census district names to pcodes", len(census_to_pcode))

    # ── 5. Compute and insert vulnerability indicators ──
    # Normalize values for composite scoring
    max_kiln_density = 1.0
    max_growth = 1.0
    for census_name, pcode in census_to_pcode.items():
        pop_data = census_pop.get(census_name, {})
        area = pop_data.get("area_sqkm", 1) or 1
        kiln_count = kiln_counts.get(pcode, 0)
        kiln_density = kiln_count / area
        max_kiln_density = max(max_kiln_density, kiln_density)
        growth = abs(pop_data.get("pop_growth", 0))
        max_growth = max(max_growth, growth)

    inserted = 0
    for census_name, pcode in census_to_pcode.items():
        pop_data = census_pop.get(census_name, {})
        population = pop_data.get("population", 0)
        area = pop_data.get("area_sqkm", 1) or 1
        urban_pct = pop_data.get("urban_proportion", 0)
        growth_rate = pop_data.get("pop_growth", 0)

        # Literacy rate
        lit_data = literacy_agg.get(census_name, {"literate": 0, "total": 0})
        literacy_rate = (lit_data["literate"] / lit_data["total"] * 100) if lit_data["total"] > 0 else None

        # Brick kilns
        kiln_count = kiln_counts.get(pcode, 0)
        kiln_density = kiln_count / area

        # Estimate under-18 population (Pakistan avg ~46% under 18)
        pop_under_18 = int(population * 0.46) if population else None

        # Compute trafficking risk score (0–1)
        literacy_factor = (1 - (literacy_rate or 50) / 100) if literacy_rate else 0.5
        kiln_factor = min(kiln_density / max_kiln_density, 1.0) if max_kiln_density > 0 else 0
        urban_factor = (1 - urban_pct / 100) if urban_pct else 0.5
        child_ratio = 0.46  # Pakistan-wide average
        growth_factor = min(abs(growth_rate) / max_growth, 1.0) if max_growth > 0 else 0

        risk_score = round(
            0.30 * literacy_factor
            + 0.25 * kiln_factor
            + 0.20 * urban_factor
            + 0.15 * child_ratio
            + 0.10 * growth_factor,
            4,
        )

        try:
            await session.execute(text("""
                INSERT INTO vulnerability_indicators
                    (district_pcode, year, literacy_rate, population_under_18,
                     brick_kiln_count, brick_kiln_density_per_sqkm,
                     trafficking_risk_score, source)
                VALUES
                    (:pcode, 2017, :literacy_rate, :pop_under_18,
                     :kiln_count, :kiln_density,
                     :risk_score, 'Census 2017 + computed')
                ON CONFLICT ON CONSTRAINT uq_vuln_district_year
                DO UPDATE SET
                    literacy_rate = EXCLUDED.literacy_rate,
                    population_under_18 = EXCLUDED.population_under_18,
                    brick_kiln_count = EXCLUDED.brick_kiln_count,
                    brick_kiln_density_per_sqkm = EXCLUDED.brick_kiln_density_per_sqkm,
                    trafficking_risk_score = EXCLUDED.trafficking_risk_score,
                    source = EXCLUDED.source
            """), {
                "pcode": pcode,
                "literacy_rate": round(literacy_rate, 2) if literacy_rate else None,
                "pop_under_18": pop_under_18,
                "kiln_count": kiln_count,
                "kiln_density": round(kiln_density, 6),
                "risk_score": risk_score,
            })
            inserted += 1
        except Exception as exc:
            logger.warning("Failed to insert vulnerability for %s: %s", pcode, exc)

    await session.commit()
    logger.info("Inserted/updated %d vulnerability indicator rows", inserted)
    return inserted


# ── Step 1D: Insert trafficking routes ───────────────────────────

async def insert_routes(session: AsyncSession) -> int:
    """Insert known trafficking routes with LineString geometry."""
    inserted = 0

    # Check for existing routes to avoid duplicates
    existing_result = await session.execute(text("SELECT route_name FROM trafficking_routes"))
    existing_names = {row[0] for row in existing_result.fetchall()}

    for route in TRAFFICKING_ROUTES:
        if route["route_name"] in existing_names:
            continue
        waypoints = route["waypoints"]
        # Build LINESTRING WKT: LINESTRING(lon1 lat1, lon2 lat2, ...)
        coords_str = ", ".join(f"{lon} {lat}" for lon, lat in waypoints)
        linestring_wkt = f"LINESTRING({coords_str})"

        try:
            await session.execute(text("""
                INSERT INTO trafficking_routes
                    (route_name, trafficking_type, origin_country, destination_country,
                     confidence_level, evidence_source, year_documented, notes,
                     route_geometry)
                VALUES
                    (:route_name, :trafficking_type, :origin_country, :destination_country,
                     :confidence_level, :evidence_source, :year_documented, :notes,
                     ST_GeomFromText(:linestring, 4326))
                ON CONFLICT DO NOTHING
            """), {
                "route_name": route["route_name"],
                "trafficking_type": route["trafficking_type"],
                "origin_country": route["origin_country"],
                "destination_country": route["destination_country"],
                "confidence_level": route["confidence_level"],
                "evidence_source": route["evidence_source"],
                "year_documented": route["year_documented"],
                "notes": route["notes"],
                "linestring": linestring_wkt,
            })
            inserted += 1
        except Exception as exc:
            logger.warning("Failed to insert route '%s': %s", route["route_name"], exc)

    await session.commit()
    logger.info("Inserted %d trafficking routes", inserted)
    return inserted


# ── Step 1E: Fix existing incidents without geometry ──────────────

async def fix_ungeocoded_incidents(session: AsyncSession, districts: dict) -> int:
    """Assign geometry to existing incidents that lack it.

    For incidents with district_pcode but no geometry: use district centroid + jitter.
    For incidents without district_pcode: assign weighted-random district + centroid.
    """
    result = await session.execute(text("""
        SELECT id, district_pcode, source_url, raw_text, location_detail
        FROM incidents
        WHERE geometry IS NULL
    """))
    rows = result.fetchall()
    logger.info("Found %d incidents without geometry", len(rows))

    fixed = 0
    for row in rows:
        district_pcode = row.district_pcode

        # Try to geocode from available text fields
        if not district_pcode:
            for field in (row.raw_text, row.location_detail, row.source_url):
                if field:
                    district_pcode = geocode_text(field, districts)
                    if district_pcode:
                        break

        # Fallback: weighted random district
        if not district_pcode:
            district_pcode = pick_weighted_district(districts)

        d = districts["by_pcode"].get(district_pcode)
        if not d or not d["centroid_lon"] or not d["centroid_lat"]:
            continue

        lon = d["centroid_lon"] + random.uniform(-0.05, 0.05)
        lat = d["centroid_lat"] + random.uniform(-0.05, 0.05)

        try:
            await session.execute(text("""
                UPDATE incidents
                SET geometry = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                    district_pcode = COALESCE(district_pcode, :pcode)
                WHERE id = :id
            """), {"id": row.id, "lon": lon, "lat": lat, "pcode": district_pcode})
            fixed += 1
        except Exception as exc:
            logger.warning("Failed to fix incident %d: %s", row.id, exc)

    await session.commit()
    logger.info("Fixed geometry for %d incidents", fixed)
    return fixed


# ── Main ─────────────────────────────────────────────────────────

async def main():
    logger.info("=" * 60)
    logger.info("Nigehbaan Data Population Script")
    logger.info("=" * 60)

    engine, SessionFactory = _build_engine()

    async with SessionFactory() as session:
        # Load districts reference data
        logger.info("Loading district boundaries...")
        districts = await load_districts(session)
        logger.info("Loaded %d districts from boundaries table", len(districts["by_pcode"]))

        if not districts["by_pcode"]:
            logger.error("No districts found in boundaries table. Run boundary loader first.")
            return

        # Step 1A: Load existing incidents
        logger.info("-" * 40)
        logger.info("Step 1A: Loading existing news incidents...")
        count_incidents = await load_existing_incidents(session, districts)

        # Step 1B: Scrape RSS feeds
        logger.info("-" * 40)
        logger.info("Step 1B: Scraping RSS feeds...")
        count_rss = await scrape_rss_feeds(session, districts)

        # Step 1C: Vulnerability indicators
        logger.info("-" * 40)
        logger.info("Step 1C: Computing vulnerability indicators...")
        count_vuln = await populate_vulnerability(session, districts)

        # Step 1D: Trafficking routes
        logger.info("-" * 40)
        logger.info("Step 1D: Inserting trafficking routes...")
        count_routes = await insert_routes(session)

        # Step 1E: Fix existing incidents without geometry
        logger.info("-" * 40)
        logger.info("Step 1E: Fixing incidents without geometry...")
        count_fixed = await fix_ungeocoded_incidents(session, districts)

        # Summary
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("  Incidents from JSON: %d", count_incidents)
        logger.info("  Incidents from RSS:  %d", count_rss)
        logger.info("  Incidents fixed:     %d", count_fixed)
        logger.info("  Vulnerability rows:  %d", count_vuln)
        logger.info("  Trafficking routes:  %d", count_routes)
        logger.info("=" * 60)

        # Quick verification
        result = await session.execute(text("SELECT COUNT(*) FROM incidents"))
        total_incidents = result.scalar()
        result = await session.execute(text("SELECT COUNT(*) FROM vulnerability_indicators"))
        total_vuln = result.scalar()
        result = await session.execute(text("SELECT COUNT(*) FROM trafficking_routes"))
        total_routes = result.scalar()
        logger.info("DB totals: %d incidents, %d vulnerability rows, %d routes",
                     total_incidents, total_vuln, total_routes)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
