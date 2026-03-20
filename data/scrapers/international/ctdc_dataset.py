"""CTDC Global Synthetic Dataset scraper for Nigehbaan data pipeline.

Wraps the existing CTDC downloader module to integrate with the
BaseAPIScraper pipeline. The Counter-Trafficking Data Collaborative
maintains 206K+ trafficking victim records worldwide; this scraper
downloads the dataset, filters Pakistan-related records, and parses
them into structured statistical_reports output.

Source: https://www.ctdatacollaborative.org/download-global-dataset
Schedule: Quarterly (0 0 1 */3 *)
Priority: P1 — Primary international trafficking dataset
"""

from datetime import datetime, timezone
from typing import Any

import logging

from data.scrapers.base_api_scraper import BaseAPIScraper
from data.downloaders.ctdc_victims import (
    download_ctdc_dataset,
    filter_pakistan_records,
    parse_ctdc_records,
)

logger = logging.getLogger(__name__)


class CTDCDatasetScraper(BaseAPIScraper):
    """Scraper for the CTDC Global Synthetic Dataset.

    Wraps the existing downloader functions in ``data.downloaders.ctdc_victims``
    to provide a standard scraper interface.  Downloads the full CSV,
    filters for Pakistan-related records, and converts them to the
    ``statistical_reports`` record format.

    Attributes:
        name: Scraper identifier.
        source_url: CTDC download page URL.
        schedule: Quarterly cron expression.
        priority: P1 core international dataset.
    """

    name: str = "ctdc_dataset"
    source_url: str = "https://www.ctdatacollaborative.org/download-global-dataset"
    schedule: str = "0 0 1 */3 *"
    priority: str = "P1"

    rate_limit_delay: float = 2.0
    request_timeout: float = 120.0

    async def scrape(self) -> list[dict[str, Any]]:
        """Download CTDC dataset, filter for Pakistan, and parse records.

        Delegates to the existing downloader pipeline:
            1. download_ctdc_dataset() -> CSV path
            2. filter_pakistan_records(csv_path) -> filtered CSV path
            3. parse_ctdc_records(filtered_path) -> list[dict]

        Returns:
            List of statistical_reports records for Pakistan-related victims.
        """
        logger.info("[%s] Starting CTDC dataset download", self.name)

        csv_path = await download_ctdc_dataset()
        if csv_path is None:
            logger.error("[%s] Failed to download CTDC dataset", self.name)
            return []

        logger.info("[%s] Dataset downloaded to %s", self.name, csv_path)

        filtered_path = filter_pakistan_records(csv_path)
        logger.info("[%s] Pakistan records filtered to %s", self.name, filtered_path)

        raw_records = parse_ctdc_records(filtered_path)
        logger.info(
            "[%s] Parsed %d Pakistan-related records", self.name, len(raw_records),
        )

        scraped_at = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []
        for raw in raw_records:
            record = {
                "source_name": "CTDC",
                "report_title": "Global Synthetic Dataset",
                "indicator": raw.get("trafficking_type", "trafficking"),
                "value": 1,
                "unit": "victim_record",
                "year": raw.get("year_of_registration", ""),
                "country": raw.get("country_of_exploitation", "Pakistan"),
                "gender": raw.get("gender", ""),
                "age_group": raw.get("age_group", ""),
                "exploitation_type": raw.get("exploitation_type", ""),
                "means_of_control": raw.get("means_of_control", ""),
                "citizenship": raw.get("country_of_citizenship", ""),
                "source_url": self.source_url,
                "scraped_at": scraped_at,
            }
            records.append(record)

        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a CTDC statistical_reports record.

        Requires source_name and at least one of indicator or report_title.
        Also checks that the record has meaningful content beyond just
        the source identifier.

        Args:
            record: A single statistical report dictionary.

        Returns:
            True if the record passes validation.
        """
        if not record.get("source_name"):
            return False
        if not (record.get("indicator") or record.get("report_title")):
            return False
        # Ensure at least one demographic or geographic field is populated
        has_detail = any(
            record.get(field)
            for field in ("country", "gender", "age_group", "exploitation_type")
        )
        return has_detail
