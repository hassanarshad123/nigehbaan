"""UNICEF SDMX API scraper for Pakistan child protection indicators.

Fetches UNICEF statistical data via the SDMX REST API for Pakistan.
Covers birth registration, child labor, and child marriage indicators
in SDMX-JSON format.

API: https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/
Schedule: Quarterly (0 6 1 */3 *)
Priority: P1 — Authoritative UNICEF child protection statistics
"""

from datetime import datetime, timezone
from typing import Any

import logging

from data.scrapers.base_api_scraper import BaseAPIScraper

logger = logging.getLogger(__name__)

SDMX_BASE_URL: str = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data"

# UNICEF SDMX dataflow definitions for Pakistan
# Each entry: (dataflow_id, description, key_filter)
DATAFLOWS: list[dict[str, str]] = [
    {
        "dataflow": "UNICEF,PT_BRTH_REG,1.0",
        "key": ".PAK...",
        "description": "Birth registration",
        "indicator_code": "PT_BRTH_REG",
    },
    {
        "dataflow": "UNICEF,PT_CHLD_Y0T14_LBR_EC,1.0",
        "key": ".PAK...",
        "description": "Child labor (economic activity, ages 0-14)",
        "indicator_code": "PT_CHLD_Y0T14_LBR_EC",
    },
    {
        "dataflow": "UNICEF,PT_F_20-24_MRD_U18,1.0",
        "key": ".PAK...",
        "description": "Child marriage (women 20-24 married before 18)",
        "indicator_code": "PT_F_20-24_MRD_U18",
    },
]


class UNICEFSDMXScraper(BaseAPIScraper):
    """Scraper for UNICEF SDMX API — Pakistan child protection data.

    Queries the UNICEF SDMX REST API for Pakistan-specific indicators
    on birth registration, child labor, and child marriage, parsing
    SDMX-JSON responses into statistical_reports formatted records.
    """

    name: str = "unicef_sdmx"
    source_url: str = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,PT_CHLD_Y0T14_LBR_EC,1.0/.PAK..."
    schedule: str = "0 6 1 */3 *"
    priority: str = "P1"
    rate_limit_delay: float = 2.0
    request_timeout: float = 60.0

    def _build_url(self, dataflow_def: dict[str, str]) -> str:
        """Construct the SDMX API URL for a given dataflow.

        Args:
            dataflow_def: Dataflow definition dict with 'dataflow' and 'key'.

        Returns:
            Full SDMX REST API URL string.
        """
        return f"{SDMX_BASE_URL}/{dataflow_def['dataflow']}/{dataflow_def['key']}"

    async def _fetch_dataflow(
        self, dataflow_def: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Fetch and parse a single SDMX dataflow for Pakistan.

        Args:
            dataflow_def: Dataflow definition with dataflow, key,
                description, and indicator_code.

        Returns:
            List of parsed observation records.
        """
        url = self._build_url(dataflow_def)
        indicator_code = dataflow_def["indicator_code"]
        description = dataflow_def["description"]

        headers = {
            "Accept": "application/vnd.sdmx.data+json;version=1.0.0-wd",
        }

        try:
            response_data = await self.fetch_json(url, headers=headers)
        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch dataflow %s: %s",
                self.name, indicator_code, exc,
            )
            return []

        if not isinstance(response_data, dict):
            logger.warning(
                "[%s] Unexpected response type for %s: %s",
                self.name, indicator_code, type(response_data),
            )
            return []

        return self._parse_sdmx_json(response_data, indicator_code, description)

    def _parse_sdmx_json(
        self,
        data: dict[str, Any],
        indicator_code: str,
        description: str,
    ) -> list[dict[str, Any]]:
        """Parse SDMX-JSON response into statistical_reports records.

        Handles the SDMX-JSON structure where observations are nested
        under dataSets[0].series, with dimension values resolved via
        the structure.dimensions.observation metadata.

        Args:
            data: Raw SDMX-JSON response dict.
            indicator_code: The UNICEF indicator code.
            description: Human-readable indicator description.

        Returns:
            List of formatted record dicts.
        """
        records: list[dict[str, Any]] = []

        # Extract the data structure
        data_sets = data.get("dataSets", [])
        if not data_sets:
            logger.warning("[%s] No dataSets in SDMX response for %s", self.name, indicator_code)
            return []

        series_dict = data_sets[0].get("series", {})
        if not series_dict:
            logger.warning("[%s] No series in SDMX response for %s", self.name, indicator_code)
            return []

        # Extract time period dimension values from structure metadata
        time_periods = self._extract_time_periods(data)
        sex_values = self._extract_dimension_values(data, "SEX")

        now = datetime.now(timezone.utc).isoformat()

        for series_key, series_data in series_dict.items():
            observations = series_data.get("observations", {})
            # Parse the series key to extract dimension indices
            dim_indices = series_key.split(":")
            sex_label = self._resolve_dimension(dim_indices, sex_values, position=1)

            for obs_index, obs_value_list in observations.items():
                if not obs_value_list or obs_value_list[0] is None:
                    continue

                value = obs_value_list[0]
                time_idx = int(obs_index)
                year = time_periods.get(time_idx, str(time_idx))

                records.append({
                    "source_name": "unicef_sdmx",
                    "report_year": year,
                    "report_title": f"UNICEF {description} — Pakistan {year}",
                    "indicator": indicator_code,
                    "indicator_label": description,
                    "value": float(value),
                    "unit": "percent",
                    "geographic_scope": "Pakistan",
                    "pdf_url": None,
                    "extraction_method": "api",
                    "extraction_confidence": 0.95,
                    "sex": sex_label,
                    "scraped_at": now,
                })

        logger.info(
            "[%s] Parsed %d observations for %s",
            self.name, len(records), indicator_code,
        )
        return records

    @staticmethod
    def _extract_time_periods(data: dict[str, Any]) -> dict[int, str]:
        """Extract time period lookup from SDMX-JSON structure metadata.

        Args:
            data: Full SDMX-JSON response.

        Returns:
            Mapping of observation index to time period string (e.g., "2018").
        """
        time_map: dict[int, str] = {}
        try:
            structure = data.get("structure", {})
            dimensions = structure.get("dimensions", {})
            obs_dims = dimensions.get("observation", [])
            for dim in obs_dims:
                if dim.get("id") == "TIME_PERIOD":
                    for idx, val in enumerate(dim.get("values", [])):
                        time_map[idx] = val.get("id", str(idx))
                    break
        except (KeyError, TypeError, IndexError):
            pass
        return time_map

    @staticmethod
    def _extract_dimension_values(
        data: dict[str, Any], dimension_id: str
    ) -> dict[int, str]:
        """Extract dimension value lookup from SDMX-JSON structure.

        Args:
            data: Full SDMX-JSON response.
            dimension_id: The dimension ID to extract (e.g., "SEX").

        Returns:
            Mapping of dimension index to label string.
        """
        value_map: dict[int, str] = {}
        try:
            structure = data.get("structure", {})
            dimensions = structure.get("dimensions", {})
            series_dims = dimensions.get("series", [])
            for dim in series_dims:
                if dim.get("id") == dimension_id:
                    for idx, val in enumerate(dim.get("values", [])):
                        value_map[idx] = val.get("name", val.get("id", str(idx)))
                    break
        except (KeyError, TypeError, IndexError):
            pass
        return value_map

    @staticmethod
    def _resolve_dimension(
        dim_indices: list[str],
        value_map: dict[int, str],
        position: int,
    ) -> str | None:
        """Resolve a dimension value from series key indices.

        Args:
            dim_indices: List of dimension index strings from the series key.
            value_map: Mapping of index to label.
            position: Position of the target dimension in the series key.

        Returns:
            Resolved label string, or None if not resolvable.
        """
        if position < len(dim_indices):
            try:
                idx = int(dim_indices[position])
                return value_map.get(idx)
            except (ValueError, IndexError):
                pass
        return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the UNICEF SDMX scraping pipeline.

        Fetches all configured dataflows sequentially (to respect rate
        limits) and combines results.

        Returns:
            List of statistical_reports records for Pakistan child
            protection indicators.
        """
        all_records: list[dict[str, Any]] = []

        for dataflow_def in DATAFLOWS:
            records = await self._fetch_dataflow(dataflow_def)
            all_records.extend(records)
            logger.info(
                "[%s] Dataflow %s: %d records",
                self.name,
                dataflow_def["indicator_code"],
                len(records),
            )

        logger.info(
            "[%s] Total: %d records across %d dataflows",
            self.name, len(all_records), len(DATAFLOWS),
        )
        return all_records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a UNICEF SDMX statistical_reports record.

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
