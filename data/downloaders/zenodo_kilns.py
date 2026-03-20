"""Zenodo brick kiln dataset downloader.

Downloads the geolocated brick kiln dataset from Zenodo. Contains
11,000+ brick kilns across Pakistan identified via satellite imagery.
Brick kilns are a primary site of bonded/child labor in Pakistan.

Dataset: ~11.8MB GeoJSON with point geometries for each kiln.
Source: https://zenodo.org/records/14038648
Output: data/raw/kilns/
Schedule: One-time download
Priority: P1 — Critical for bonded labor spatial analysis
"""

from pathlib import Path
from typing import Any

import json
import logging

import httpx

logger = logging.getLogger(__name__)

RAW_KILNS_DIR = Path("data/raw/kilns")

ZENODO_RECORD_ID: str = "14038648"
ZENODO_API_URL: str = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

# Pakistan approximate bounding box (lat, lng)
_PAK_LAT_MIN: float = 23.5
_PAK_LAT_MAX: float = 37.5
_PAK_LNG_MIN: float = 60.0
_PAK_LNG_MAX: float = 77.5

# Streaming chunk size for large file download
_STREAM_CHUNK_SIZE: int = 64 * 1024  # 64 KB


async def download_kiln_dataset(
    output_dir: Path = RAW_KILNS_DIR,
) -> Path | None:
    """Download the Zenodo brick kiln GeoJSON dataset.

    Downloads the complete dataset of 11,000+ geolocated brick
    kilns in Pakistan. Each point includes coordinates and
    classification confidence.

    Args:
        output_dir: Directory to save the downloaded file.

    Returns:
        Path to the downloaded GeoJSON file, or None on failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Nigehbaan-DataPipeline/1.0 "
                "(Anti-Trafficking Research; +https://nigehbaan.pk)"
            ),
        },
    ) as client:
        # Step 1: Query Zenodo API for record metadata
        logger.info("Fetching Zenodo record metadata from %s", ZENODO_API_URL)
        try:
            response = await client.get(ZENODO_API_URL)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch Zenodo record metadata: %s", exc)
            return None

        record = response.json()
        files = record.get("files", [])
        if not files:
            logger.error("No files found in Zenodo record %s", ZENODO_RECORD_ID)
            return None

        # Step 2: Find the GeoJSON file in the record
        target_file = None
        for file_entry in files:
            file_key = file_entry.get("key", "")
            if file_key.lower().endswith(".geojson") or file_key.lower().endswith(".json"):
                target_file = file_entry
                break

        # Fallback: take the first/largest file
        if target_file is None:
            target_file = max(files, key=lambda f: f.get("size", 0))
            logger.warning(
                "No GeoJSON file found by extension; using largest file: %s",
                target_file.get("key", "unknown"),
            )

        # Extract download URL
        download_url = target_file.get("links", {}).get("self")
        if not download_url:
            # Build URL from key
            bucket = record.get("links", {}).get("bucket")
            if bucket:
                download_url = f"{bucket}/{target_file['key']}"
            else:
                download_url = (
                    f"https://zenodo.org/records/{ZENODO_RECORD_ID}"
                    f"/files/{target_file['key']}"
                )

        file_name = target_file.get("key", "brick_kilns.geojson")
        if not file_name.endswith(".geojson"):
            file_name = "brick_kilns.geojson"
        output_path = output_dir / file_name

        # Step 3: Stream download (file is ~11.8MB)
        logger.info(
            "Downloading kiln dataset (%s bytes) from %s",
            target_file.get("size", "unknown"),
            download_url,
        )
        try:
            async with client.stream("GET", download_url) as stream:
                stream.raise_for_status()
                with open(output_path, "wb") as f:
                    async for chunk in stream.aiter_bytes(chunk_size=_STREAM_CHUNK_SIZE):
                        f.write(chunk)
        except httpx.HTTPError as exc:
            logger.error("Failed to download kiln dataset: %s", exc)
            return None

        # Step 4: Validate
        if validate_kiln_geojson(output_path):
            logger.info("Successfully downloaded and validated kiln dataset: %s", output_path)
            return output_path
        else:
            logger.warning(
                "Kiln dataset downloaded but validation failed: %s", output_path
            )
            # Return path anyway — data may still be partially usable
            return output_path


def get_record_metadata() -> dict[str, Any]:
    """Fetch Zenodo record metadata for the kiln dataset.

    Returns:
        Dict with title, doi, file_size, download_url.
    """
    try:
        with httpx.Client(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Nigehbaan-DataPipeline/1.0 "
                    "(Anti-Trafficking Research; +https://nigehbaan.pk)"
                ),
            },
        ) as client:
            response = client.get(ZENODO_API_URL)
            response.raise_for_status()

        record = response.json()
        files = record.get("files", [])

        # Find GeoJSON file
        geojson_file = None
        for f in files:
            if f.get("key", "").lower().endswith((".geojson", ".json")):
                geojson_file = f
                break
        if geojson_file is None and files:
            geojson_file = files[0]

        download_url = ""
        file_size = 0
        if geojson_file:
            download_url = geojson_file.get("links", {}).get("self", "")
            file_size = geojson_file.get("size", 0)

        return {
            "title": record.get("metadata", {}).get("title", ""),
            "doi": record.get("doi", ""),
            "file_size": file_size,
            "download_url": download_url,
            "created": record.get("created", ""),
            "updated": record.get("updated", ""),
        }
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch Zenodo record metadata: %s", exc)
        return {}


def validate_kiln_geojson(file_path: Path) -> bool:
    """Validate the downloaded kiln GeoJSON.

    Checks that the file contains valid GeoJSON with Point
    geometries and a reasonable number of features (>10,000).

    Args:
        file_path: Path to the GeoJSON file.

    Returns:
        True if valid with expected structure.
    """
    if not file_path.exists():
        logger.warning("Kiln GeoJSON file does not exist: %s", file_path)
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Invalid JSON in %s: %s", file_path, exc)
        return False

    # Check FeatureCollection type
    if data.get("type") != "FeatureCollection":
        logger.warning(
            "Expected FeatureCollection, got '%s' in %s",
            data.get("type"),
            file_path,
        )
        return False

    features = data.get("features", [])

    # Check feature count > 10000
    if len(features) < 10000:
        logger.warning(
            "Expected >10,000 features, found %d in %s",
            len(features),
            file_path,
        )
        return False

    # Sample features to check geometry type and coordinates
    sample_size = min(100, len(features))
    point_count = 0
    in_pakistan_count = 0

    for feature in features[:sample_size]:
        geometry = feature.get("geometry", {})
        geom_type = geometry.get("type", "")
        coords = geometry.get("coordinates", [])

        if geom_type == "Point":
            point_count += 1

            # Check coordinates are within Pakistan bounds
            # GeoJSON uses [longitude, latitude] order
            if len(coords) >= 2:
                lng, lat = coords[0], coords[1]
                if (
                    _PAK_LAT_MIN <= lat <= _PAK_LAT_MAX
                    and _PAK_LNG_MIN <= lng <= _PAK_LNG_MAX
                ):
                    in_pakistan_count += 1

    # At least 80% of sampled features should be Points
    if point_count < sample_size * 0.8:
        logger.warning(
            "Only %d/%d sampled features are Points in %s",
            point_count,
            sample_size,
            file_path,
        )
        return False

    # At least 70% of sampled points should be within Pakistan bounds
    if in_pakistan_count < point_count * 0.7:
        logger.warning(
            "Only %d/%d sampled points are within Pakistan bounds in %s",
            in_pakistan_count,
            point_count,
            file_path,
        )
        return False

    logger.info(
        "Kiln GeoJSON validation passed: %d features, %d/%d points in Pakistan",
        len(features),
        in_pakistan_count,
        sample_size,
    )
    return True


def compute_district_kiln_counts(
    kiln_geojson_path: Path,
    boundaries_geojson_path: Path,
) -> dict[str, int]:
    """Spatial join: count kilns per district.

    Performs a point-in-polygon spatial join to count how many
    kilns fall within each district boundary.

    Args:
        kiln_geojson_path: Path to kiln point GeoJSON.
        boundaries_geojson_path: Path to district boundary GeoJSON.

    Returns:
        Dict mapping district P-code to kiln count.
    """
    try:
        import geopandas as gpd
    except ImportError:
        logger.error(
            "geopandas is required for spatial join. "
            "Install with: pip install geopandas"
        )
        return {}

    if not kiln_geojson_path.exists():
        logger.error("Kiln GeoJSON not found: %s", kiln_geojson_path)
        return {}

    if not boundaries_geojson_path.exists():
        logger.error("Boundaries GeoJSON not found: %s", boundaries_geojson_path)
        return {}

    try:
        # Load kiln points
        logger.info("Loading kiln points from %s", kiln_geojson_path)
        kilns_gdf = gpd.read_file(kiln_geojson_path)

        # Load district boundaries
        logger.info("Loading district boundaries from %s", boundaries_geojson_path)
        districts_gdf = gpd.read_file(boundaries_geojson_path)

        # Ensure both GeoDataFrames use the same CRS
        if kilns_gdf.crs != districts_gdf.crs:
            kilns_gdf = kilns_gdf.to_crs(districts_gdf.crs)

        # Find the P-code column in boundaries
        pcode_col = None
        for col in districts_gdf.columns:
            col_lower = col.lower()
            if "pcode" in col_lower and ("adm2" in col_lower or "admin2" in col_lower):
                pcode_col = col
                break
        if pcode_col is None:
            for col in districts_gdf.columns:
                if "pcode" in col.lower():
                    pcode_col = col
                    break
        if pcode_col is None:
            logger.error(
                "No P-code column found in boundaries. Columns: %s",
                list(districts_gdf.columns),
            )
            return {}

        # Perform spatial join: points within polygons
        logger.info("Performing spatial join (kilns -> districts)")
        joined = gpd.sjoin(
            kilns_gdf,
            districts_gdf[[pcode_col, "geometry"]],
            how="inner",
            predicate="within",
        )

        # Count kilns per district
        counts = joined.groupby(pcode_col).size().to_dict()

        logger.info(
            "Spatial join complete: %d kilns matched across %d districts",
            sum(counts.values()),
            len(counts),
        )
        return {str(k): int(v) for k, v in counts.items()}

    except Exception as exc:
        logger.error("Spatial join failed: %s", exc)
        return {}
