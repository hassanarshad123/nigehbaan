"""DHS Program API scraper for Pakistan child protection indicators.

Fetches Demographic and Health Surveys (DHS) data for Pakistan from
the DHS Program REST API. Covers child marriage and child labor
indicators disaggregated by survey year.

API: https://api.dhsprogram.com/rest/dhs/data
Schedule: Quarterly (0 5 1 */3 *)
Priority: P1 — Primary survey-based child protection statistics
"""

from datetime import datetime, timezone
from typing import Any

import logging

from data.scrapers.base_api_scraper import BaseAPIScraper

logger = logging.getLogger(__name__)

# DHS indicator codes for child protection in Pakistan
# Note: Use MA_MBAY_* (not CM_ECMW_*) as those have actual PK data
INDICATOR_IDS: dict[str, str] = {
    "MA_MBAY_W_B15": "Young women age 20-24 first married by exact age 15",
    "MA_MBAY_W_B18": "Young women age 20-24 first married by exact age 18",
    "MA_MBAY_M_B18": "Young men age 20-24 first married by exact age 18",
    "MA_MBAG_W_B15": "Women first married by exact age 15",
    "MA_MBAG_W_B18": "Women first married by exact age 18",
}

COUNTRY_CODE: str = "PK"
API_BASE_URL: str = "https://api.dhsprogram.com/rest/dhs/data"


class DHSAPIScraper(BaseAPIScraper):
    """Scraper for DHS Program API — Pakistan child marriage and labor data.

    Queries the DHS REST API for Pakistan-specific indicators on
    child marriage (CM_ECMW_C_MRG, CM_ECMW_C_M15) and child labor
    (CL_CHLD_W_CHL), returning statistical_reports formatted records.
    """

    name: str = "dhs_api"
    source_url: str = "https://api.dhsprogram.com/rest/dhs/data"
    schedule: str = "0 5 1 */3 *"
    priority: str = "P1"
    rate_limit_delay: float = 1.0

    async def fetch_indicators(self) -> list[dict[str, Any]]:
        """Fetch all configured DHS indicators for Pakistan.

        Returns:
            Combined list of observation records across all indicators.
        """
        indicator_ids_param = ",".join(INDICATOR_IDS.keys())
        params: dict[str, str] = {
            "countryIds": COUNTRY_CODE,
            "indicatorIds": indicator_ids_param,
            "returnFields": (
                "Indicator,IndicatorId,Value,SurveyYear,"
                "SurveyType,CharacteristicLabel,ByVariableLabel,"
                "DenominatorWeighted,IsPreferred"
            ),
            "f": "json",
        }

        try:
            response_data = await self.fetch_json(API_BASE_URL, params=params)
        except Exception as exc:
            logger.error("[%s] API request failed: %s", self.name, exc)
            return []

        if not isinstance(response_data, dict):
            logger.warning("[%s] Unexpected response type: %s", self.name, type(response_data))
            return []

        data_rows = response_data.get("Data", [])
        if not data_rows:
            logger.warning("[%s] No data rows returned from DHS API", self.name)
            return []

        logger.info("[%s] Received %d data points from DHS API", self.name, len(data_rows))
        return data_rows

    @staticmethod
    def _to_record(row: dict[str, Any]) -> dict[str, Any] | None:
        """Convert a single DHS API row to a statistical_reports record.

        Args:
            row: Raw data point from DHS API response.

        Returns:
            Formatted record dict, or None if the row lacks required fields.
        """
        value = row.get("Value")
        if value is None or value == "":
            return None

        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return None

        indicator_id = row.get("IndicatorId", "")
        indicator_label = row.get("Indicator", indicator_id)
        survey_year = row.get("SurveyYear")
        characteristic = row.get("CharacteristicLabel", "")
        by_variable = row.get("ByVariableLabel", "")

        title_parts = [f"DHS Pakistan {survey_year}", indicator_label]
        if characteristic:
            title_parts.append(characteristic)

        return {
            "source_name": "dhs_api",
            "report_year": str(survey_year) if survey_year else None,
            "report_title": " — ".join(title_parts),
            "indicator": indicator_id,
            "indicator_label": indicator_label,
            "value": numeric_value,
            "unit": "percent",
            "geographic_scope": "Pakistan",
            "pdf_url": None,
            "extraction_method": "api",
            "extraction_confidence": 0.95,
            "characteristic": characteristic,
            "by_variable": by_variable,
            "is_preferred": row.get("IsPreferred", False),
            "denominator_weighted": row.get("DenominatorWeighted"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the DHS API scraping pipeline.

        Returns:
            List of statistical_reports records for Pakistan child
            marriage and child labor indicators.
        """
        raw_rows = await self.fetch_indicators()
        if not raw_rows:
            return []

        records: list[dict[str, Any]] = []
        for row in raw_rows:
            record = self._to_record(row)
            if record is not None:
                records.append(record)

        logger.info(
            "[%s] Produced %d records from %d raw data points",
            self.name, len(records), len(raw_rows),
        )
        return records

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a DHS statistical_reports record.

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
