"""Download foundation datasets for Nigehbaan.

Downloads:
1. HDX Pakistan Admin Boundaries (COD-AB) -- GeoJSON admin levels 0-3
2. Zenodo Brick Kiln Dataset -- GeoJSON ~11K points

Usage:
    python scripts/download_foundation_data.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
BOUNDARIES_DIR = ROOT / "data" / "raw" / "boundaries"
KILNS_DIR = ROOT / "data" / "raw" / "kilns"

# ── HDX config ───────────────────────────────────────────────────
HDX_CKAN_API = "https://data.humdata.org/api/3/action/package_show"
HDX_DATASET_ID = "cod-ab-pak"

# Expected filename stems from HDX COD-AB Pakistan.  The CKAN API
# returns a list of resources; we match on the filename pattern.
HDX_FILENAME_PATTERNS: dict[str, str] = {
    "pak_admbnda_adm0": "pak_admin0.geojson",
    "pak_admbnda_adm1": "pak_admin1.geojson",
    "pak_admbnda_adm2": "pak_admin2.geojson",
    "pak_admbnda_adm3": "pak_admin3.geojson",
}

# Fallback direct-download resource IDs (HDX stable URLs)
HDX_FALLBACK_RESOURCES: dict[str, str] = {
    "pak_admin0.geojson": "https://data.humdata.org/dataset/cod-ab-pak/resource/7e107ef7-e3b0-4607-8394-ba5216677833/download",
    "pak_admin1.geojson": "https://data.humdata.org/dataset/cod-ab-pak/resource/3f15e49e-3e79-40e0-8fec-d7c38cad3837/download",
    "pak_admin2.geojson": "https://data.humdata.org/dataset/cod-ab-pak/resource/5e663f3b-5076-4a5f-8f0d-2a85aae2b2b2/download",
    "pak_admin3.geojson": "https://data.humdata.org/dataset/cod-ab-pak/resource/0d218eaf-00a2-4119-855f-23b076e78e91/download",
}

# ── Zenodo config ────────────────────────────────────────────────
ZENODO_RECORD_API = "https://zenodo.org/api/records/14038648"

# ── HTTP settings ────────────────────────────────────────────────
TIMEOUT = httpx.Timeout(60.0, connect=15.0)
HEADERS = {
    "User-Agent": "Nigehbaan-DataLoader/1.0 (child-protection-research)"
}


# ── Download helpers ─────────────────────────────────────────────


def _ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def _download_file(client: httpx.Client, url: str, dest: Path) -> bool:
    """Stream-download a file to disk. Returns True on success."""
    try:
        logger.info("  Downloading %s -> %s", url[:120], dest.name)
        with client.stream("GET", url, follow_redirects=True) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65_536):
                    f.write(chunk)
        size_mb = dest.stat().st_size / (1024 * 1024)
        logger.info("  Saved %s (%.1f MB)", dest.name, size_mb)
        return True
    except httpx.HTTPStatusError as exc:
        logger.error("  HTTP %d for %s", exc.response.status_code, url[:120])
        return False
    except Exception as exc:
        logger.error("  Download failed: %s", exc)
        return False


def _validate_geojson(path: Path) -> bool:
    """Check that a file is valid GeoJSON with features."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("type") != "FeatureCollection":
            logger.warning("  %s: not a FeatureCollection", path.name)
            return False
        feature_count = len(data.get("features", []))
        if feature_count == 0:
            logger.warning("  %s: zero features", path.name)
            return False
        logger.info("  Validated %s: %d features", path.name, feature_count)
        return True
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("  Invalid JSON in %s: %s", path.name, exc)
        return False


# ── HDX download ─────────────────────────────────────────────────


def _download_hdx_boundaries(client: httpx.Client) -> int:
    """Download HDX COD-AB Pakistan admin boundary GeoJSON files.

    Returns count of successfully downloaded/validated files.
    """
    _ensure_dir(BOUNDARIES_DIR)
    downloaded = 0

    # Try CKAN API first to get fresh resource URLs
    resource_urls: dict[str, str] = {}
    try:
        logger.info("Querying HDX CKAN API for %s ...", HDX_DATASET_ID)
        resp = client.get(
            HDX_CKAN_API,
            params={"id": HDX_DATASET_ID},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        resources = payload.get("result", {}).get("resources", [])
        logger.info("  Found %d resources in dataset", len(resources))

        for res in resources:
            res_name = (res.get("name") or "").lower()
            res_url = res.get("url") or res.get("download_url") or ""
            res_format = (res.get("format") or "").lower()

            # Only interested in GeoJSON resources
            if res_format not in ("geojson", "json"):
                continue

            for pattern, local_name in HDX_FILENAME_PATTERNS.items():
                if pattern.lower() in res_name.lower() or pattern.lower() in res_url.lower():
                    resource_urls[local_name] = res_url
                    break

    except Exception as exc:
        logger.warning("HDX CKAN API failed (%s), using fallback URLs", exc)

    # Download each admin level
    for local_name in HDX_FILENAME_PATTERNS.values():
        dest = BOUNDARIES_DIR / local_name

        # Skip if already exists and valid
        if dest.exists() and _validate_geojson(dest):
            logger.info("  %s already exists and is valid, skipping", local_name)
            downloaded += 1
            continue

        url = resource_urls.get(local_name) or HDX_FALLBACK_RESOURCES.get(local_name, "")
        if not url:
            logger.error("  No URL found for %s", local_name)
            continue

        if _download_file(client, url, dest):
            if _validate_geojson(dest):
                downloaded += 1
            else:
                logger.error("  Downloaded %s but validation failed", local_name)
                dest.unlink(missing_ok=True)
        else:
            # Try fallback if primary URL failed
            fallback = HDX_FALLBACK_RESOURCES.get(local_name, "")
            if fallback and fallback != url:
                logger.info("  Trying fallback URL for %s ...", local_name)
                if _download_file(client, fallback, dest) and _validate_geojson(dest):
                    downloaded += 1

    return downloaded


# ── Zenodo download ──────────────────────────────────────────────


def _download_zenodo_kilns(client: httpx.Client) -> bool:
    """Download the Zenodo brick kiln GeoJSON dataset.

    Returns True if file is available and valid.
    """
    _ensure_dir(KILNS_DIR)

    # Check if already downloaded
    existing = list(KILNS_DIR.glob("*.geojson"))
    if existing:
        for f in existing:
            if _validate_geojson(f):
                logger.info("Kiln data already exists: %s", f.name)
                return True

    # Query Zenodo API for file list
    dest_name = "brick_kilns_zenodo.geojson"
    dest = KILNS_DIR / dest_name

    try:
        logger.info("Querying Zenodo API for record 14038648 ...")
        resp = client.get(ZENODO_RECORD_API, timeout=TIMEOUT)
        resp.raise_for_status()
        record = resp.json()

        files = record.get("files", [])
        logger.info("  Found %d files in Zenodo record", len(files))

        # Find the GeoJSON file
        geojson_url = None
        for file_entry in files:
            filename = file_entry.get("key", "").lower()
            if filename.endswith(".geojson") or filename.endswith(".json"):
                geojson_url = file_entry.get("links", {}).get("self", "")
                if not geojson_url:
                    # Construct URL from bucket
                    bucket = record.get("links", {}).get("bucket", "")
                    if bucket:
                        geojson_url = f"{bucket}/{file_entry['key']}"
                logger.info("  Found GeoJSON: %s", file_entry.get("key"))
                break

        if not geojson_url:
            logger.error("  No GeoJSON file found in Zenodo record")
            return False

        if _download_file(client, geojson_url, dest):
            return _validate_geojson(dest)

    except Exception as exc:
        logger.error("Zenodo API/download failed: %s", exc)

    return False


# ── Main ─────────────────────────────────────────────────────────


def main() -> int:
    """Download all foundation datasets. Returns 0 on success."""
    logger.info("=" * 60)
    logger.info("Nigehbaan Foundation Data Downloader")
    logger.info("=" * 60)

    success = True

    with httpx.Client(headers=HEADERS, timeout=TIMEOUT) as client:
        # 1. HDX Admin Boundaries
        logger.info("")
        logger.info("STEP 1: HDX Pakistan Admin Boundaries (COD-AB)")
        logger.info("-" * 50)
        boundary_count = _download_hdx_boundaries(client)
        expected = len(HDX_FILENAME_PATTERNS)
        logger.info(
            "Boundaries: %d/%d files ready", boundary_count, expected
        )
        if boundary_count < expected:
            logger.warning(
                "Some boundary files missing -- bootstrap_data.py "
                "will skip missing admin levels"
            )
            success = False

        # 2. Zenodo Brick Kilns
        logger.info("")
        logger.info("STEP 2: Zenodo Brick Kiln Dataset")
        logger.info("-" * 50)
        kilns_ok = _download_zenodo_kilns(client)
        if kilns_ok:
            logger.info("Brick kiln data: ready")
        else:
            logger.warning("Brick kiln data: NOT available")
            success = False

    # Summary
    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("All foundation data downloaded successfully.")
    else:
        logger.warning(
            "Some downloads failed. Run bootstrap_data.py anyway -- "
            "it handles missing files gracefully."
        )
    logger.info("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
