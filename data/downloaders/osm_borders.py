"""OSM border crossing points downloader.

Downloads Pakistan shapefiles from Geofabrik and extracts border
crossing points (barrier=border_control). Border crossings are
important for tracking cross-border trafficking routes.

Source: https://download.geofabrik.de/asia/pakistan.html
Output: data/raw/osm/
Schedule: Monthly (border data updates infrequently)
Priority: P2 — Cross-border trafficking route analysis
"""

from pathlib import Path
from typing import Any

import json
import logging
import zipfile

import httpx

logger = logging.getLogger(__name__)

RAW_OSM_DIR = Path("data/raw/osm")

GEOFABRIK_URL: str = (
    "https://download.geofabrik.de/asia/pakistan-latest-free.shp.zip"
)

# Streaming chunk size for the large ZIP download (~100-200MB)
_STREAM_CHUNK_SIZE: int = 128 * 1024  # 128 KB

# Approximate border segments for Pakistan's neighbors.
# Each entry defines the rough geographic region (lat/lng ranges)
# where that country's border with Pakistan lies.
_BORDER_REGIONS: dict[str, dict[str, tuple[float, float]]] = {
    "Afghanistan": {
        "lat": (29.0, 37.0),
        "lng": (60.0, 71.5),
    },
    "Iran": {
        "lat": (25.0, 29.5),
        "lng": (60.0, 63.5),
    },
    "India": {
        "lat": (23.5, 37.0),
        "lng": (71.5, 77.5),
    },
    "China": {
        "lat": (35.5, 37.5),
        "lng": (74.0, 77.5),
    },
}


async def download_pakistan_shapefiles(
    output_dir: Path = RAW_OSM_DIR,
) -> Path | None:
    """Download Pakistan shapefiles from Geofabrik.

    Downloads the complete Pakistan OSM extract as shapefiles.
    The download is a ZIP archive containing multiple shapefiles
    for different feature types.

    Args:
        output_dir: Directory to save and extract the download.

    Returns:
        Path to the extracted directory, or None on failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "pakistan-latest-free.shp.zip"
    extract_dir = output_dir / "pakistan-shapefiles"

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(600.0),  # 10 min for large file
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Nigehbaan-DataPipeline/1.0 "
                "(Anti-Trafficking Research; +https://nigehbaan.pk)"
            ),
        },
    ) as client:
        # Download the ZIP using streaming for the large file
        logger.info("Downloading Pakistan shapefiles from %s", GEOFABRIK_URL)
        try:
            async with client.stream("GET", GEOFABRIK_URL) as stream:
                stream.raise_for_status()
                total_size = int(stream.headers.get("content-length", 0))
                downloaded_bytes = 0

                with open(zip_path, "wb") as f:
                    async for chunk in stream.aiter_bytes(chunk_size=_STREAM_CHUNK_SIZE):
                        f.write(chunk)
                        downloaded_bytes += len(chunk)

                if total_size > 0:
                    logger.info(
                        "Download complete: %d bytes (expected %d)",
                        downloaded_bytes,
                        total_size,
                    )
                else:
                    logger.info("Download complete: %d bytes", downloaded_bytes)

        except httpx.HTTPError as exc:
            logger.error("Failed to download Pakistan shapefiles: %s", exc)
            # Clean up partial download
            if zip_path.exists():
                zip_path.unlink()
            return None

    # Extract the ZIP
    logger.info("Extracting shapefiles to %s", extract_dir)
    try:
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        logger.info("Extraction complete: %d files", len(list(extract_dir.rglob("*"))))
    except zipfile.BadZipFile as exc:
        logger.error("Downloaded file is not a valid ZIP: %s", exc)
        return None
    except Exception as exc:
        logger.error("Failed to extract shapefiles: %s", exc)
        return None

    # Verify extraction produced shapefiles
    shp_files = list(extract_dir.rglob("*.shp"))
    if not shp_files:
        logger.error("No .shp files found after extraction in %s", extract_dir)
        return None

    logger.info(
        "Successfully extracted %d shapefiles to %s",
        len(shp_files),
        extract_dir,
    )

    # Optionally remove the ZIP to save space
    try:
        zip_path.unlink()
        logger.info("Removed ZIP archive: %s", zip_path)
    except OSError:
        logger.debug("Could not remove ZIP archive: %s", zip_path)

    return extract_dir


def extract_border_crossings(
    shapefile_dir: Path,
) -> list[dict[str, Any]]:
    """Extract border crossing points from OSM data.

    Filters OSM features for barrier=border_control tag to
    identify international border crossing points.

    Args:
        shapefile_dir: Directory containing extracted shapefiles.

    Returns:
        List of border crossing point records with name, lat,
        lng, osm_id, border_country fields.
    """
    try:
        import geopandas as gpd
    except ImportError:
        logger.error(
            "geopandas is required for shapefile processing. "
            "Install with: pip install geopandas"
        )
        return []

    if not shapefile_dir.exists():
        logger.error("Shapefile directory does not exist: %s", shapefile_dir)
        return []

    crossings: list[dict[str, Any]] = []

    # Find point shapefiles — border crossings are typically point features
    point_shapefiles = list(shapefile_dir.rglob("*point*.shp"))
    if not point_shapefiles:
        # Fallback: try all shapefiles
        point_shapefiles = list(shapefile_dir.rglob("*.shp"))

    for shp_path in point_shapefiles:
        try:
            gdf = gpd.read_file(shp_path)
        except Exception as exc:
            logger.warning("Could not read shapefile %s: %s", shp_path, exc)
            continue

        if gdf.empty:
            continue

        # Normalize column names to lowercase for matching
        col_map = {c: c.lower() for c in gdf.columns}
        gdf_lower_cols = gdf.rename(columns=col_map)

        # Filter for border crossing features
        # OSM tags: barrier=border_control, boundary=border_point
        mask = None
        for tag_col, tag_val in [
            ("barrier", "border_control"),
            ("boundary", "border_point"),
            ("border", "yes"),
        ]:
            if tag_col in gdf_lower_cols.columns:
                col_mask = gdf_lower_cols[tag_col].astype(str).str.lower() == tag_val
                mask = col_mask if mask is None else (mask | col_mask)

        # Also check fclass/type columns common in Geofabrik extracts
        for type_col in ("fclass", "type", "ftype"):
            if type_col in gdf_lower_cols.columns:
                col_mask = gdf_lower_cols[type_col].astype(str).str.lower().isin(
                    ["border_control", "border_point", "border_crossing"]
                )
                mask = col_mask if mask is None else (mask | col_mask)

        if mask is None or not mask.any():
            continue

        filtered = gdf[mask]
        logger.info(
            "Found %d border crossing features in %s",
            len(filtered),
            shp_path.name,
        )

        for _, row in filtered.iterrows():
            geom = row.geometry
            if geom is None:
                continue

            # Extract centroid coordinates
            try:
                lng = float(geom.x)
                lat = float(geom.y)
            except AttributeError:
                # For non-point geometries, use centroid
                centroid = geom.centroid
                lng = float(centroid.x)
                lat = float(centroid.y)

            # Extract name from various possible columns
            name = ""
            for name_col in ("name", "name_en", "nam", "label"):
                original_col = None
                for orig, lower in col_map.items():
                    if lower == name_col:
                        original_col = orig
                        break
                if original_col and original_col in gdf.columns:
                    val = row.get(original_col)
                    if val and str(val).lower() not in ("nan", "none", ""):
                        name = str(val).strip()
                        break

            # Extract OSM ID
            osm_id = ""
            for id_col_name in ("osm_id", "id", "fid", "gid"):
                for orig, lower in col_map.items():
                    if lower == id_col_name:
                        val = row.get(orig)
                        if val and str(val).lower() not in ("nan", "none", ""):
                            osm_id = str(val).strip()
                            break
                if osm_id:
                    break

            border_country = identify_border_country(lat, lng)

            crossings.append({
                "name": name,
                "lat": lat,
                "lng": lng,
                "osm_id": osm_id,
                "border_country": border_country,
                "source_file": shp_path.name,
            })

    logger.info("Extracted %d border crossings total", len(crossings))
    return crossings


def identify_border_country(
    lat: float, lng: float
) -> str | None:
    """Identify which neighboring country a border crossing faces.

    Uses coordinate proximity to determine if the crossing is
    on the Afghanistan, Iran, India, or China border.

    Args:
        lat: Latitude of the border crossing.
        lng: Longitude of the border crossing.

    Returns:
        Neighboring country name, or None if undetermined.
    """
    best_match: str | None = None
    best_score: float = 0.0

    for country, region in _BORDER_REGIONS.items():
        lat_range = region["lat"]
        lng_range = region["lng"]

        # Check if the point falls within this country's border region
        in_lat = lat_range[0] <= lat <= lat_range[1]
        in_lng = lng_range[0] <= lng <= lng_range[1]

        if not (in_lat and in_lng):
            continue

        # For overlapping regions, score by proximity to the border edge.
        # Points closer to the edge of Pakistan's territory are more
        # likely to be border crossings with that country.
        score = 0.0

        if country == "Afghanistan":
            # Western/northwestern border: lower longitude = closer to Afghanistan
            score = max(0.0, 71.5 - lng) / 11.5
        elif country == "Iran":
            # Southwestern border: lower longitude and lower latitude
            score = max(0.0, 63.5 - lng) / 3.5
        elif country == "India":
            # Eastern border: higher longitude = closer to India
            score = max(0.0, lng - 71.5) / 6.0
        elif country == "China":
            # Northeastern corner: high lat and high lng
            lat_score = max(0.0, lat - 35.5) / 2.0
            lng_score = max(0.0, lng - 74.0) / 3.5
            score = (lat_score + lng_score) / 2.0

        if score > best_score:
            best_score = score
            best_match = country

    return best_match


def save_border_crossings_geojson(
    crossings: list[dict[str, Any]],
    output_path: Path | None = None,
) -> Path:
    """Save extracted border crossings as GeoJSON.

    Args:
        crossings: List of border crossing records.
        output_path: Path for output file.

    Returns:
        Path to the saved GeoJSON file.
    """
    output_file = output_path or (RAW_OSM_DIR / "border_crossings.geojson")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    features: list[dict[str, Any]] = []
    for crossing in crossings:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [crossing["lng"], crossing["lat"]],
            },
            "properties": {
                "name": crossing.get("name", ""),
                "osm_id": crossing.get("osm_id", ""),
                "border_country": crossing.get("border_country"),
                "source_file": crossing.get("source_file", ""),
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    output_file.write_text(
        json.dumps(geojson, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(
        "Saved %d border crossings to %s",
        len(features),
        output_file,
    )
    return output_file
