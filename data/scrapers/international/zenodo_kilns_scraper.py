"""Zenodo brick kiln dataset scraper (wraps existing downloader).

Wraps the existing data.downloaders.zenodo_kilns module to integrate
the 11,000+ geolocated brick kiln dataset into the standard scraper
pipeline. Produces summary statistics (total kilns, kilns per province
bucket) as statistical_reports records.

Brick kilns in Pakistan are a primary site of bonded and child labor,
employing an estimated 4.5 million workers including ~1.5 million children.

Source: https://zenodo.org/records/14038648
Schedule: One-time (0 0 1 1 *)
Priority: P1 — Critical spatial data for bonded labor analysis
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import json
import logging

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Pakistan province bounding boxes (approximate lat/lng ranges)
# Used to bucket kiln points into provinces without a full spatial join
_PROVINCE_BOUNDS: dict[str, dict[str, float]] = {
    "Punjab": {"lat_min": 28.0, "lat_max": 34.0, "lng_min": 69.5, "lng_max": 75.5},
    "Sindh": {"lat_min": 24.0, "lat_max": 28.0, "lng_min": 66.5, "lng_max": 71.0},
    "Khyber Pakhtunkhwa": {"lat_min": 33.5, "lat_max": 37.0, "lng_min": 69.0, "lng_max": 73.0},
    "Balochistan": {"lat_min": 25.0, "lat_max": 32.0, "lng_min": 60.5, "lng_max": 70.0},
    "Islamabad Capital Territory": {"lat_min": 33.5, "lat_max": 33.9, "lng_min": 72.8, "lng_max": 73.3},
}

RAW_KILNS_DIR = Path("data/raw/kilns")


class ZenodoKilnsScraper(BaseScraper):
    """Scraper that wraps the existing Zenodo kiln dataset downloader.

    Calls download_kiln_dataset(), loads the resulting GeoJSON, computes
    summary statistics, and produces statistical_reports records with
    total kiln counts and per-province breakdowns.
    """

    name: str = "zenodo_kilns_scraper"
    source_url: str = "https://zenodo.org/records/14038648"
    schedule: str = "0 0 1 1 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0
    request_timeout: float = 180.0  # large file download

    async def scrape(self) -> list[dict[str, Any]]:
        """Download kiln dataset and produce summary records."""
        from data.downloaders.zenodo_kilns import download_kiln_dataset, validate_kiln_geojson

        logger.info("[%s] Calling download_kiln_dataset()", self.name)
        geojson_path = await download_kiln_dataset(output_dir=RAW_KILNS_DIR)

        if geojson_path is None:
            logger.error("[%s] download_kiln_dataset() returned None", self.name)
            return []

        if not geojson_path.exists():
            logger.error("[%s] GeoJSON file does not exist: %s", self.name, geojson_path)
            return []

        # Validate the downloaded file
        is_valid = validate_kiln_geojson(geojson_path)
        if not is_valid:
            logger.warning(
                "[%s] GeoJSON validation failed; proceeding with available data",
                self.name,
            )

        # Load and analyze features
        features = self._load_features(geojson_path)
        if not features:
            logger.warning("[%s] No features found in GeoJSON", self.name)
            return []

        total_kilns = len(features)
        logger.info("[%s] Loaded %d kiln features", self.name, total_kilns)

        province_counts = self._count_by_province(features)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Build summary records
        records: list[dict[str, Any]] = []

        # Total kilns record
        records.append({
            "source_name": self.name,
            "report_year": str(datetime.now(timezone.utc).year),
            "report_title": "Zenodo Brick Kiln Dataset — Pakistan Summary",
            "indicator": "total_kilns",
            "value": total_kilns,
            "unit": "count",
            "geographic_scope": "Pakistan",
            "pdf_url": None,
            "extraction_method": "geojson_feature_count",
            "extraction_confidence": 0.95 if is_valid else 0.60,
            "victim_gender": None,
            "victim_age_bracket": None,
            "geojson_path": str(geojson_path),
            "scraped_at": now_iso,
        })

        # Per-province records
        for province, count in province_counts.items():
            records.append({
                "source_name": self.name,
                "report_year": str(datetime.now(timezone.utc).year),
                "report_title": f"Zenodo Brick Kiln Dataset — {province}",
                "indicator": "kilns_per_province",
                "value": count,
                "unit": "count",
                "geographic_scope": province,
                "pdf_url": None,
                "extraction_method": "geojson_bbox_bucketing",
                "extraction_confidence": 0.70,
                "victim_gender": None,
                "victim_age_bracket": None,
                "geojson_path": str(geojson_path),
                "scraped_at": now_iso,
            })

        # Unclassified kilns (outside all province bounding boxes)
        classified = sum(province_counts.values())
        unclassified = total_kilns - classified
        if unclassified > 0:
            records.append({
                "source_name": self.name,
                "report_year": str(datetime.now(timezone.utc).year),
                "report_title": "Zenodo Brick Kiln Dataset — Unclassified Region",
                "indicator": "kilns_per_province",
                "value": unclassified,
                "unit": "count",
                "geographic_scope": "Pakistan (unclassified region)",
                "pdf_url": None,
                "extraction_method": "geojson_bbox_bucketing",
                "extraction_confidence": 0.50,
                "victim_gender": None,
                "victim_age_bracket": None,
                "geojson_path": str(geojson_path),
                "scraped_at": now_iso,
            })

        return records

    @staticmethod
    def _load_features(geojson_path: Path) -> list[dict[str, Any]]:
        """Load features from a GeoJSON file."""
        try:
            content = geojson_path.read_text(encoding="utf-8")
            data = json.loads(content)
            return data.get("features", [])
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            logger.error("Failed to load GeoJSON from %s: %s", geojson_path, exc)
            return []

    @staticmethod
    def _count_by_province(
        features: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Bucket kiln features into provinces using bounding boxes.

        This is an approximation; for precise classification use
        the spatial join in data.downloaders.zenodo_kilns.
        """
        counts: dict[str, int] = {prov: 0 for prov in _PROVINCE_BOUNDS}

        for feature in features:
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [])
            if not coords or len(coords) < 2:
                continue

            lng, lat = coords[0], coords[1]

            for province, bounds in _PROVINCE_BOUNDS.items():
                if (
                    bounds["lat_min"] <= lat <= bounds["lat_max"]
                    and bounds["lng_min"] <= lng <= bounds["lng_max"]
                ):
                    counts[province] += 1
                    break

        # Remove provinces with zero count
        return {k: v for k, v in counts.items() if v > 0}

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a Zenodo kilns summary record."""
        if not record.get("source_name"):
            return False
        if not record.get("indicator"):
            return False
        if record.get("value") is None or record["value"] < 0:
            return False
        return True
