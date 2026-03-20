#!/usr/bin/env python3
"""Master pipeline script: download foundation data and load into Neon DB.

Usage:
    cd "F:/Zensbot_Producst/CHILD TRAFFICING"
    python -m data.pipeline_run [--download] [--load] [--all]

Flags:
    --download   Download foundation datasets (boundaries, kilns, borders, census)
    --load       Load downloaded data into Neon PostgreSQL
    --all        Run both download and load (default if no flags given)
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger("pipeline")


async def download_all() -> dict[str, bool]:
    """Download all P0 foundation datasets."""
    results: dict[str, bool] = {}

    # 1A. HDX Boundaries
    logger.info("=== Downloading HDX Administrative Boundaries ===")
    try:
        from data.downloaders.hdx_boundaries import download_hdx_boundaries
        downloaded = await download_hdx_boundaries()
        results["boundaries"] = len(downloaded) > 0
        logger.info("Boundaries: downloaded %d levels", len(downloaded))
    except Exception as exc:
        logger.error("Boundaries download failed: %s", exc)
        results["boundaries"] = False

    # 1B. Zenodo Brick Kilns
    logger.info("=== Downloading Zenodo Brick Kiln Dataset ===")
    try:
        from data.downloaders.zenodo_kilns import download_kiln_dataset
        kiln_path = await download_kiln_dataset()
        results["kilns"] = kiln_path is not None
        logger.info("Kilns: %s", kiln_path or "FAILED")
    except Exception as exc:
        logger.error("Kilns download failed: %s", exc)
        results["kilns"] = False

    # 1C. Border crossings (fallback data already exists)
    border_file = ROOT / "data" / "raw" / "osm" / "border_crossings.geojson"
    results["borders"] = border_file.exists()
    logger.info("Border crossings: %s (fallback file)", "EXISTS" if results["borders"] else "MISSING")

    # 1D. Census 2017
    logger.info("=== Cloning Census 2017 Repository ===")
    try:
        from data.downloaders.census_2017 import clone_census_repo
        repo_path = await clone_census_repo()
        results["census"] = repo_path is not None
        logger.info("Census: %s", repo_path or "FAILED")
    except Exception as exc:
        logger.error("Census clone failed: %s", exc)
        results["census"] = False

    return results


async def load_all() -> dict[str, dict[str, int]]:
    """Load all downloaded data into Neon PostgreSQL."""
    results: dict[str, dict[str, int]] = {}

    # 3A. Load boundaries FIRST (other tables FK to boundaries.pcode)
    logger.info("=== Loading Boundaries ===")
    try:
        from data.loaders.boundaries_loader import BoundariesLoader
        loader = BoundariesLoader()
        results["boundaries"] = await loader.run_all_levels()
        logger.info("Boundaries: %s", results["boundaries"])
    except Exception as exc:
        logger.error("Boundaries load failed: %s", exc)
        results["boundaries"] = {"loaded": 0, "skipped": 0, "errors": 1}

    # 3B. Load brick kilns
    logger.info("=== Loading Brick Kilns ===")
    try:
        from data.loaders.kilns_loader import KilnsLoader
        loader = KilnsLoader()
        results["kilns"] = await loader.run()
        logger.info("Kilns: %s", results["kilns"])
    except Exception as exc:
        logger.error("Kilns load failed: %s", exc)
        results["kilns"] = {"loaded": 0, "skipped": 0, "errors": 1}

    # 3C. Load border crossings
    logger.info("=== Loading Border Crossings ===")
    try:
        from data.loaders.borders_loader import BordersLoader
        loader = BordersLoader()
        results["borders"] = await loader.run()
        logger.info("Borders: %s", results["borders"])
    except Exception as exc:
        logger.error("Borders load failed: %s", exc)
        results["borders"] = {"loaded": 0, "skipped": 0, "errors": 1}

    # 3D. Load incidents (if any parsed incident files exist)
    logger.info("=== Loading Incidents ===")
    try:
        from data.loaders.incidents_loader import IncidentsLoader
        loader = IncidentsLoader()
        incident_files = loader.discover_files()
        if incident_files:
            results["incidents"] = await loader.run()
        else:
            logger.info("No incident files found — skipping")
            results["incidents"] = {"loaded": 0, "skipped": 0, "errors": 0}
        logger.info("Incidents: %s", results["incidents"])
    except Exception as exc:
        logger.error("Incidents load failed: %s", exc)
        results["incidents"] = {"loaded": 0, "skipped": 0, "errors": 1}

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Nigehbaan data pipeline")
    parser.add_argument("--download", action="store_true", help="Download foundation datasets")
    parser.add_argument("--load", action="store_true", help="Load data into Neon DB")
    parser.add_argument("--all", action="store_true", help="Download + load (default)")
    args = parser.parse_args()

    run_all = args.all or (not args.download and not args.load)

    if run_all or args.download:
        download_results = await download_all()
        logger.info("\n=== Download Summary ===")
        for name, success in download_results.items():
            logger.info("  %s: %s", name, "OK" if success else "FAILED")

    if run_all or args.load:
        load_results = await load_all()
        logger.info("\n=== Load Summary ===")
        for name, counts in load_results.items():
            logger.info("  %s: %s", name, counts)

    logger.info("\nPipeline complete!")


if __name__ == "__main__":
    asyncio.run(main())
