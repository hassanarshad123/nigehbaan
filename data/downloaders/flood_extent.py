"""UNOSAT 2022 flood extent shapefile downloader.

Source: https://data.humdata.org (UNOSAT flood extent datasets)
Output: data/raw/flood/
Priority: P2
"""

from pathlib import Path
from typing import Any
import io
import zipfile

import logging

import httpx

logger = logging.getLogger(__name__)

RAW_FLOOD_DIR = Path("data/raw/flood")
HDX_FLOOD_DATASET: str = "pakistan-flood-extent-2022"
HDX_API_URL: str = "https://data.humdata.org/api/3/action/package_show"


async def download_flood_extent(
    output_dir: Path = RAW_FLOOD_DIR,
) -> Path | None:
    """Download UNOSAT 2022 flood extent shapefiles."""
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(
        timeout=120.0, follow_redirects=True,
        headers={"User-Agent": "Nigehbaan-DataPipeline/1.0"},
    ) as client:
        try:
            # Query HDX for the flood dataset
            params = {"id": HDX_FLOOD_DATASET}
            response = await client.get(HDX_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                # Try alternate dataset names
                for alt_id in [
                    "pakistan-flood-response-2022",
                    "pakistan-floods-2022-extent",
                    "unosat-flood-extent-pakistan",
                ]:
                    try:
                        resp = await client.get(HDX_API_URL, params={"id": alt_id})
                        alt_data = resp.json()
                        if alt_data.get("success"):
                            data = alt_data
                            break
                    except Exception:
                        continue

            resources = data.get("result", {}).get("resources", [])
            shapefile_resources = [
                r for r in resources
                if any(ext in r.get("url", "").lower() for ext in [".shp", ".zip", "shapefile"])
                or "shapefile" in r.get("format", "").lower()
                or "shape" in r.get("name", "").lower()
            ]

            if not shapefile_resources:
                shapefile_resources = [
                    r for r in resources
                    if r.get("url", "").lower().endswith(".zip")
                ]

            for resource in shapefile_resources:
                url = resource.get("url", "")
                if not url:
                    continue
                try:
                    logger.info("Downloading flood extent: %s", url)
                    file_response = await client.get(url)
                    file_response.raise_for_status()

                    if url.lower().endswith(".zip"):
                        with zipfile.ZipFile(io.BytesIO(file_response.content)) as zf:
                            zf.extractall(output_dir)
                        logger.info("Extracted flood shapefiles to %s", output_dir)
                    else:
                        filename = Path(url).name
                        file_path = output_dir / filename
                        file_path.write_bytes(file_response.content)

                    return output_dir

                except Exception as exc:
                    logger.warning("Failed to download %s: %s", url, exc)

            logger.warning("No flood extent shapefiles found on HDX")
            return None

        except Exception as exc:
            logger.error("Error downloading flood extent: %s", exc)
            return None


def calculate_district_flood_percentage(
    flood_extent_path: Path,
    district_boundaries_path: Path,
) -> dict[str, float]:
    """Calculate percentage of each district affected by flooding."""
    try:
        import geopandas as gpd
    except ImportError:
        logger.error("geopandas not installed")
        return {}

    try:
        # Load flood extent
        flood_files = list(flood_extent_path.glob("*.shp"))
        if not flood_files:
            logger.warning("No shapefiles found in %s", flood_extent_path)
            return {}
        flood_gdf = gpd.read_file(flood_files[0])

        # Load district boundaries
        districts_gdf = gpd.read_file(district_boundaries_path)

        # Ensure same CRS
        if flood_gdf.crs != districts_gdf.crs:
            flood_gdf = flood_gdf.to_crs(districts_gdf.crs)

        # Calculate flood percentage for each district
        pcode_col = next(
            (c for c in districts_gdf.columns if "PCODE" in c.upper() and "ADM2" in c.upper()),
            None,
        )
        if not pcode_col:
            pcode_col = next(
                (c for c in districts_gdf.columns if "pcode" in c.lower()),
                districts_gdf.columns[0],
            )

        results: dict[str, float] = {}
        for _, district in districts_gdf.iterrows():
            pcode = district[pcode_col]
            district_area = district.geometry.area
            if district_area <= 0:
                continue

            try:
                intersection = flood_gdf.geometry.intersection(district.geometry)
                flood_area = intersection.area.sum()
                percentage = (flood_area / district_area) * 100.0
                results[pcode] = round(min(percentage, 100.0), 2)
            except Exception:
                results[pcode] = 0.0

        return results

    except Exception as exc:
        logger.error("Error calculating flood percentages: %s", exc)
        return {}


def classify_flood_impact(
    flood_percentages: dict[str, float],
) -> dict[str, str]:
    """Classify district flood impact into severity categories."""
    classifications: dict[str, str] = {}
    for pcode, percentage in flood_percentages.items():
        if percentage > 50:
            classifications[pcode] = "severe"
        elif percentage > 25:
            classifications[pcode] = "high"
        elif percentage > 10:
            classifications[pcode] = "moderate"
        elif percentage > 1:
            classifications[pcode] = "low"
        else:
            classifications[pcode] = "minimal"
    return classifications


def save_flood_analysis(
    flood_data: dict[str, float],
    output_path: Path | None = None,
) -> Path:
    """Save flood analysis results as CSV."""
    import csv

    out_path = output_path or RAW_FLOOD_DIR / "district_flood_analysis.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    classifications = classify_flood_impact(flood_data)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["district_pcode", "flood_percentage", "severity"])
        for pcode, percentage in sorted(flood_data.items()):
            writer.writerow([pcode, percentage, classifications.get(pcode, "unknown")])

    logger.info("Saved flood analysis to %s", out_path)
    return out_path
