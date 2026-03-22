"""CTDC Global Synthetic Dataset scraper for Nigehbaan data pipeline.

Wraps the existing CTDC downloader module to integrate with the
BaseAPIScraper pipeline. The Counter-Trafficking Data Collaborative
maintains 206K+ trafficking victim records worldwide; this scraper
downloads the dataset, filters Pakistan-related records, and parses
them into structured statistical_reports output.

Source: https://www.ctdatacollaborative.org/download-global-dataset
Schedule: Quarterly (0 0 1 */3 *)
Priority: P1 — Primary international trafficking dataset

Updated 2026-03-22: Fixed to handle CTDC site restructuring.
- Added direct CSV download as fallback in scraper itself
- Improved Pakistan filtering with PAK / 586 country codes
- Made download failures non-fatal (returns empty list with warning)
- Added self-contained CSV download when downloader module fails
"""

from datetime import datetime, timezone
from typing import Any

import csv
import io
import logging

from data.scrapers.base_api_scraper import BaseAPIScraper
from data.downloaders.ctdc_victims import (
    download_ctdc_dataset,
    filter_pakistan_records,
    parse_ctdc_records,
)

logger = logging.getLogger(__name__)

# Pakistan identifiers for self-contained fallback filtering
_PAKISTAN_IDS = {"pakistan", "pak", "586"}


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

    # Direct CSV URLs to try if the downloader module fails
    FALLBACK_CSV_URLS: list[str] = [
        "https://www.ctdatacollaborative.org/sites/default/files/Global_Synthetic_Data.csv",
        "https://www.ctdatacollaborative.org/sites/default/files/global_synthetic_dataset.csv",
        "https://www.ctdatacollaborative.org/sites/default/files/CTDC_Global_Synthetic.csv",
    ]

    async def _download_via_module(self) -> list[dict[str, Any]]:
        """Use the ctdc_victims downloader module pipeline."""
        csv_path = await download_ctdc_dataset()
        if csv_path is None:
            return []

        logger.info("[%s] Dataset downloaded to %s", self.name, csv_path)

        filtered_path = filter_pakistan_records(csv_path)
        logger.info("[%s] Pakistan records filtered to %s", self.name, filtered_path)

        raw_records = parse_ctdc_records(filtered_path)
        logger.info(
            "[%s] Parsed %d Pakistan-related records", self.name, len(raw_records),
        )
        return raw_records

    async def _download_fallback(self) -> list[dict[str, Any]]:
        """Self-contained fallback: download CSV directly and filter inline."""
        raw_dir = self.get_raw_dir()
        raw_dir.mkdir(parents=True, exist_ok=True)

        for csv_url in self.FALLBACK_CSV_URLS:
            try:
                logger.info("[%s] Trying fallback CSV: %s", self.name, csv_url)
                response = await self.fetch(csv_url)
                text = response.text

                # Validate it looks like CSV
                if not text or len(text) < 500:
                    continue
                first_char = text.strip()[0] if text.strip() else ""
                if first_char in ("<", "{", "["):
                    continue

                # Save raw CSV
                csv_path = raw_dir / "ctdc_global_synthetic.csv"
                csv_path.write_text(text, encoding="utf-8")
                logger.info(
                    "[%s] Downloaded CSV via fallback (%d bytes)",
                    self.name, len(text),
                )

                # Parse and filter for Pakistan inline
                return self._filter_csv_for_pakistan(text)

            except Exception as exc:
                logger.debug(
                    "[%s] Fallback CSV %s failed: %s", self.name, csv_url, exc
                )

        return []

    def _filter_csv_for_pakistan(self, csv_text: str) -> list[dict[str, Any]]:
        """Filter CSV text for Pakistan-related rows and return parsed records."""
        records: list[dict[str, Any]] = []
        reader = csv.DictReader(io.StringIO(csv_text))

        if reader.fieldnames is None:
            return records

        # Identify country columns
        country_cols = [
            c for c in reader.fieldnames
            if any(
                kw in c.lower()
                for kw in [
                    "country", "citizenship", "exploitation",
                    "origin", "nationality", "destination",
                ]
            )
        ]

        for row in reader:
            # Check if any country column contains a Pakistan identifier
            is_pakistan = False
            for col in country_cols:
                val = (row.get(col) or "").lower().strip()
                if val in _PAKISTAN_IDS or "pakistan" in val:
                    is_pakistan = True
                    break

            if not is_pakistan:
                continue

            # Map to standard field names
            col_lower = {k.lower().strip(): k for k in row.keys()}

            def _get(possible: list[str]) -> str:
                for p in possible:
                    actual = col_lower.get(p)
                    if actual and row.get(actual):
                        return row[actual]
                return ""

            records.append({
                "trafficking_type": _get(["typeoftrafficking", "trafficking_type", "type_trafficking"]),
                "exploitation_type": _get(["typeofexploitation", "exploitation_type", "type_exploitation"]),
                "gender": _get(["gender", "sex"]),
                "age_group": _get(["agebroad", "age_group", "age_broad", "agegroup"]),
                "country_of_exploitation": _get(["countryofexploitation", "country_exploitation"]),
                "country_of_citizenship": _get(["citizenship", "countryofcitizenship", "nationality"]),
                "means_of_control": _get(["meansofcontrol", "means_control"]),
                "year_of_registration": _get(["yearofregistration", "year_registration", "year"]),
                "source": "CTDC",
            })

        logger.info(
            "[%s] Inline CSV filter found %d Pakistan records", self.name, len(records)
        )
        return records

    async def scrape(self) -> list[dict[str, Any]]:
        """Download CTDC dataset, filter for Pakistan, and parse records.

        Strategy order:
        1. Use the ctdc_victims downloader module pipeline
        2. Self-contained fallback CSV download + inline filtering

        Returns:
            List of statistical_reports records for Pakistan-related victims.
        """
        logger.info("[%s] Starting CTDC dataset download", self.name)

        # Strategy 1: Use the downloader module
        try:
            raw_records = await self._download_via_module()
        except Exception as exc:
            logger.warning(
                "[%s] Downloader module failed: %s — trying fallback",
                self.name, exc,
            )
            raw_records = []

        # Strategy 2: Self-contained fallback
        if not raw_records:
            logger.info("[%s] Trying self-contained CSV download fallback", self.name)
            try:
                raw_records = await self._download_fallback()
            except Exception as exc:
                logger.warning(
                    "[%s] Fallback download also failed: %s", self.name, exc
                )
                raw_records = []

        if not raw_records:
            logger.warning(
                "[%s] No Pakistan records found from any source — returning empty",
                self.name,
            )
            return []

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

        logger.info("[%s] Returning %d statistical_reports records", self.name, len(records))
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
