"""Loader for news article data → news_articles table."""

from typing import Any
from data.loaders.base_loader import BaseLoader


class NewsLoader(BaseLoader):
    name = "news_loader"
    source_dir = "news"
    table_name = "news_articles"

    def transform(self, raw_record: dict[str, Any]) -> dict[str, Any] | None:
        url = raw_record.get("url")
        if not url:
            return None
        return {
            "source_name": raw_record.get("source", raw_record.get("source_feed")),
            "url": url,
            "title": raw_record.get("title"),
            "published_date": raw_record.get("published_date"),
            "full_text": raw_record.get("full_text"),
            "is_trafficking_relevant": True,
            "relevance_score": raw_record.get("relevance_score"),
        }

    def validate(self, record: dict[str, Any]) -> bool:
        return bool(record.get("url") and record.get("title"))
