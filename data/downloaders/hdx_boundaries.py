"""HDX COD-AB administrative boundaries downloader.

Downloads the Common Operational Dataset for Administrative
Boundaries (COD-AB) from HDX (Humanitarian Data Exchange).
Provides GeoJSON/Shapefile boundary data at admin levels 0-3.

This is a P0 FOUNDATION dataset — it must be downloaded before
any other geographic data can be processed.

Admin levels:
    - Level 0: Country boundary (Pakistan)
    - Level 1: Provinces (Punjab, Sindh, KP, Balochistan, etc.)
    - Level 2: Districts (~160 districts)
    - Level 3: Tehsils/Talukas (~600+ subdivisions)

Source: https://data.humdata.org/dataset/cod-ab-pak
Output: data/raw/boundaries/
Schedule: One-time download (re-download if updated)
Priority: P0
"""

from pathlib import Path
from typing import Any

import json
import logging

import httpx

logger = logging.getLogger(__name__)

# Output directory for boundary files
RAW_BOUNDARIES_DIR = Path("data/raw/boundaries")

HDX_DATASET_ID: str = "cod-ab-pak"
HDX_API_URL: str = (
    f"https://data.humdata.org/api/3/action/package_show?id={HDX_DATASET_ID}"
)

# Admin level keywords used to match resource names to admin levels
_ADMIN_LEVEL_PATTERNS: dict[str, list[str]] = {
    "adm0": ["adm0", "admin0", "adm_0", "level0", "level_0", "country"],
    "adm1": ["adm1", "admin1", "adm_1", "level1", "level_1", "province"],
    "adm2": ["adm2", "admin2", "adm_2", "level2", "level_2", "district"],
    "adm3": ["adm3", "admin3", "adm_3", "level3", "level_3", "tehsil"],
}


def _match_admin_level(resource_name: str) -> str | None:
    """Match a resource name to an admin level identifier.

    Args:
        resource_name: The HDX resource name or filename.

    Returns:
        Admin level key (e.g. 'adm2') or None if no match.
    """
    name_lower = resource_name.lower()
    for level_key, patterns in _ADMIN_LEVEL_PATTERNS.items():
        for pattern in patterns:
            if pattern in name_lower:
                return level_key
    return None


async def download_hdx_boundaries(
    output_dir: Path = RAW_BOUNDARIES_DIR,
) -> dict[str, Path]:
    """Download HDX COD-AB admin boundary files for Pakistan.

    Downloads GeoJSON files for all admin levels (0-3) from the
    HDX dataset. These boundaries are the spatial foundation for
    all geographic analysis in Nigehbaan.

    Args:
        output_dir: Directory to save downloaded files.

    Returns:
        Dict mapping admin level names to their file paths.
        Example: {"adm0": Path("data/raw/boundaries/pak_adm0.geojson")}
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: dict[str, Path] = {}

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(60.0),
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Nigehbaan-DataPipeline/1.0 "
                "(Anti-Trafficking Research; +https://nigehbaan.pk)"
            ),
        },
    ) as client:
        # Fetch dataset metadata from HDX CKAN API
        logger.info("Fetching HDX COD-AB dataset metadata from %s", HDX_API_URL)
        try:
            response = await client.get(HDX_API_URL)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch HDX dataset metadata: %s", exc)
            return downloaded

        payload = response.json()
        if not payload.get("success"):
            logger.error("HDX API returned unsuccessful response")
            return downloaded

        resources = payload.get("result", {}).get("resources", [])
        if not resources:
            logger.error("No resources found in HDX COD-AB dataset")
            return downloaded

        # Filter for GeoJSON resources and match to admin levels
        geojson_resources: list[tuple[str, str]] = []
        for resource in resources:
            url = resource.get("url", "")
            name = resource.get("name", "") or resource.get("description", "")
            fmt = (resource.get("format", "") or "").lower()

            # Prefer GeoJSON files
            is_geojson = (
                fmt in ("geojson", "json")
                or url.lower().endswith(".geojson")
                or url.lower().endswith(".json")
                or "geojson" in name.lower()
            )
            if not is_geojson:
                continue

            level = _match_admin_level(name) or _match_admin_level(url)
            if level and level not in {lvl for lvl, _ in geojson_resources}:
                geojson_resources.append((level, url))

        if not geojson_resources:
            # Fallback: try all resources that look geographic
            logger.warning(
                "No GeoJSON resources matched by name; "
                "attempting to download any geographic resource"
            )
            for resource in resources:
                url = resource.get("url", "")
                name = resource.get("name", "") or resource.get("description", "")
                level = _match_admin_level(name) or _match_admin_level(url)
                if level and level not in {lvl for lvl, _ in geojson_resources}:
                    geojson_resources.append((level, url))

        # Download each matched resource
        for level, url in geojson_resources:
            file_name = f"pak_{level}.geojson"
            file_path = output_dir / file_name

            logger.info("Downloading %s boundary from %s", level, url)
            try:
                dl_response = await client.get(url)
                dl_response.raise_for_status()
                file_path.write_bytes(dl_response.content)

                if validate_geojson(file_path):
                    downloaded[level] = file_path
                    logger.info(
                        "Successfully downloaded and validated %s -> %s",
                        level,
                        file_path,
                    )
                else:
                    logger.warning(
                        "Downloaded %s but GeoJSON validation failed: %s",
                        level,
                        file_path,
                    )
                    # Keep the file but still record it
                    downloaded[level] = file_path
            except httpx.HTTPError as exc:
                logger.error("Failed to download %s from %s: %s", level, url, exc)

    logger.info(
        "HDX boundaries download complete: %d/%d levels",
        len(downloaded),
        len(_ADMIN_LEVEL_PATTERNS),
    )
    return downloaded


async def download_specific_level(
    level: int, output_dir: Path = RAW_BOUNDARIES_DIR
) -> Path | None:
    """Download boundaries for a specific admin level.

    Args:
        level: Admin level (0, 1, 2, or 3).
        output_dir: Directory to save downloaded file.

    Returns:
        Path to the downloaded file, or None on failure.
    """
    if level not in (0, 1, 2, 3):
        logger.error("Invalid admin level: %d. Must be 0, 1, 2, or 3.", level)
        return None

    target_key = f"adm{level}"
    results = await download_hdx_boundaries(output_dir)

    return results.get(target_key)


def validate_geojson(file_path: Path) -> bool:
    """Validate that a downloaded file is valid GeoJSON.

    Args:
        file_path: Path to the GeoJSON file.

    Returns:
        True if the file is valid GeoJSON with features.
    """
    if not file_path.exists():
        logger.warning("GeoJSON file does not exist: %s", file_path)
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Invalid JSON in %s: %s", file_path, exc)
        return False

    # Check for FeatureCollection type
    geojson_type = data.get("type", "")
    if geojson_type != "FeatureCollection":
        logger.warning(
            "GeoJSON type is '%s', expected 'FeatureCollection' in %s",
            geojson_type,
            file_path,
        )
        return False

    # Check for features array
    features = data.get("features")
    if not isinstance(features, list):
        logger.warning("No 'features' array found in %s", file_path)
        return False

    if len(features) == 0:
        logger.warning("Empty features array in %s", file_path)
        return False

    # Check that features have non-empty geometry fields
    valid_features = 0
    for feature in features[:10]:  # Sample first 10 for performance
        geometry = feature.get("geometry")
        if geometry and geometry.get("type") and geometry.get("coordinates"):
            valid_features += 1

    if valid_features == 0:
        logger.warning("No features with valid geometry found in %s", file_path)
        return False

    logger.info(
        "GeoJSON validation passed for %s: %d features",
        file_path,
        len(features),
    )
    return True


def get_dataset_metadata() -> dict[str, Any]:
    """Fetch metadata about the HDX COD-AB Pakistan dataset.

    Returns:
        Dict with dataset name, last_modified date, resource
        count, and resource URLs.
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
            response = client.get(HDX_API_URL)
            response.raise_for_status()

        payload = response.json()
        if not payload.get("success"):
            logger.error("HDX API returned unsuccessful response")
            return {}

        result = payload.get("result", {})
        resources = result.get("resources", [])

        return {
            "name": result.get("name", ""),
            "title": result.get("title", ""),
            "last_modified": result.get("metadata_modified", ""),
            "resource_count": len(resources),
            "resources": [
                {
                    "name": r.get("name", ""),
                    "format": r.get("format", ""),
                    "url": r.get("url", ""),
                    "size": r.get("size"),
                    "last_modified": r.get("last_modified", ""),
                }
                for r in resources
            ],
        }
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch HDX dataset metadata: %s", exc)
        return {}
