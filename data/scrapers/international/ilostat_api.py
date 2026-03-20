"""ILOSTAT bulk CSV API scraper for child labor indicators.

Fetches ILO SDG indicator 8.7.1 (child labor rate by sex and age group)
for Pakistan from the ILOSTAT bulk download facility. The indicator
SDG_0871_SEX_AGE_RT provides child labor prevalence rates disaggregated
by sex and age bracket — the authoritative global measure.

Source: https://ilostat.ilo.org/data/bulk/
Schedule: Quarterly (0 4 1 */3 *)
Priority: P1 — Primary global child labor statistics
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import logging

from data.scrapers.base_api_scraper import BaseAPIScraper

logger = logging.getLogger(__name__)

INDICATOR_ID: str = "SDG_0871_SEX_AGE_RT"
BULK_CSV_URL: str = f"https://ilostat.ilo.org/data/bulk/{INDICATOR_ID}.csv.gz"
PAKISTAN_REF_AREA: str = "PAK"

# Column mapping from ILOSTAT CSV headers to our record format
_SEX_MAP: dict[str, str] = {
    "SEX_T": "total",
    "SEX_M": "male",
    "SEX_F": "female",
}

_AGE_MAP: dict[str, str] = {
    "AGE_Y5-14": "5-14",
    "AGE_Y5-17": "5-17",
    "AGE_Y7-14": "7-14",
    "AGE_Y15-17": "15-17",
}


class ILOSTATAPIScraper(BaseAPIScraper):
    """Scraper for ILOSTAT SDG 8.7.1 child labor indicator (Pakistan).

    Downloads the bulk CSV for indicator SDG_0871_SEX_AGE_RT, filters
    rows for ref_area=PAK, and maps each observation to the
    statistical_reports record format.
    """

    name: str = "ilostat_api"
    source_url: str = "https://ilostat.ilo.org/data/bulk/"
    schedule: str = "0 4 1 */3 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0
    request_timeout: float = 120.0  # bulk CSV can be large

    async def scrape(self) -> list[dict[str, Any]]:
        """Download bulk CSV and extract Pakistan child labor rows."""
        logger.info("[%s] Downloading ILOSTAT bulk CSV: %s", self.name, BULK_CSV_URL)

        csv_path = await self._download_and_decompress()
        if csv_path is None:
            logger.warning("[%s] Failed to obtain CSV data", self.name)
            return []

        raw_rows = self.parse_csv(csv_path)
        logger.info("[%s] Parsed %d total rows from bulk CSV", self.name, len(raw_rows))

        pak_rows = [
            row for row in raw_rows
            if row.get("ref_area") == PAKISTAN_REF_AREA
        ]
        logger.info("[%s] Filtered to %d Pakistan rows", self.name, len(pak_rows))

        records = [self._to_record(row) for row in pak_rows]
        return [r for r in records if r is not None]

    async def _download_and_decompress(self) -> Path | None:
        """Download the gzipped CSV and decompress to local storage."""
        import gzip

        raw_dir = self.get_raw_dir()
        gz_path = raw_dir / f"{INDICATOR_ID}_{self.run_id}.csv.gz"
        csv_path = raw_dir / f"{INDICATOR_ID}_{self.run_id}.csv"

        try:
            content = await self.fetch_bytes(BULK_CSV_URL)
            gz_path.write_bytes(content)
            logger.info(
                "[%s] Downloaded %d bytes to %s",
                self.name, len(content), gz_path,
            )
        except Exception as exc:
            logger.error("[%s] Download failed: %s", self.name, exc)
            return None

        try:
            with gzip.open(gz_path, "rb") as gz_in:
                decompressed = gz_in.read()
            csv_path.write_bytes(decompressed)
            logger.info("[%s] Decompressed to %s", self.name, csv_path)
        except Exception as exc:
            logger.error("[%s] Decompression failed: %s", self.name, exc)
            return None

        return csv_path

    @staticmethod
    def _to_record(row: dict[str, str]) -> dict[str, Any] | None:
        """Convert a single ILOSTAT CSV row to a statistical_reports record."""
        obs_value = row.get("obs_value", "").strip()
        if not obs_value:
            return None

        try:
            value = float(obs_value)
        except ValueError:
            return None

        sex_code = row.get("sex", "")
        age_code = row.get("classif1", "")
        year = row.get("time", "")

        return {
            "source_name": "ilostat_api",
            "report_year": year,
            "report_title": f"SDG 8.7.1 Child Labor Rate — Pakistan {year}",
            "indicator": "child_labor_rate_sdg_8_7_1",
            "value": value,
            "unit": "percent",
            "geographic_scope": "Pakistan",
            "pdf_url": None,
            "extraction_method": "ilostat_bulk_csv",
            "extraction_confidence": 0.95,
            "victim_gender": _SEX_MAP.get(sex_code, sex_code),
            "victim_age_bracket": _AGE_MAP.get(age_code, age_code),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an ILOSTAT record.

        Requires source_name, indicator, a numeric value, and a report year.
        """
        if not record.get("source_name"):
            return False
        if not record.get("indicator"):
            return False
        if record.get("value") is None:
            return False
        if not record.get("report_year"):
            return False
        return True
