"""Loader for TIP Report data → tip_report_annual table."""

from typing import Any
from data.loaders.base_loader import BaseLoader


class TIPLoader(BaseLoader):
    name = "tip_loader"
    source_dir = "tip_report"
    table_name = "tip_report_annual"

    def transform(self, raw_record: dict[str, Any]) -> dict[str, Any] | None:
        year = raw_record.get("year")
        if not year:
            return None
        return {
            "year": int(year),
            "tier_ranking": raw_record.get("tier_ranking"),
            "investigations": raw_record.get("investigations"),
            "prosecutions": raw_record.get("prosecutions"),
            "convictions": raw_record.get("convictions"),
            "victims_identified": raw_record.get("victims_identified"),
            "victims_assisted": raw_record.get("victims_assisted"),
            "source_url": raw_record.get("url"),
        }

    def validate(self, record: dict[str, Any]) -> bool:
        return bool(record.get("year") and record.get("tier_ranking"))
