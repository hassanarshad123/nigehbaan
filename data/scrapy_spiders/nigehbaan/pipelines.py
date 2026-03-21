"""Scrapy pipelines for writing items to the Nigehbaan PostgreSQL database."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CourtJudgmentPipeline:
    """Save court judgment items to JSON files for later DB import.

    Uses file-based output to avoid SQLAlchemy async/Twisted conflicts.
    The Celery task that launches the spider handles DB insertion after crawl completes.
    """

    def open_spider(self, spider):
        output_dir = Path("data/raw") / f"scrapy_{spider.name}"
        output_dir.mkdir(parents=True, exist_ok=True)
        self._output_path = output_dir / "latest_crawl.json"
        self._items: list[dict] = []

    def close_spider(self, spider):
        self._output_path.write_text(
            json.dumps(self._items, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(
            "[%s] Saved %d items to %s",
            spider.name, len(self._items), self._output_path,
        )

    def process_item(self, item, spider):
        self._items.append(dict(item))
        return item
