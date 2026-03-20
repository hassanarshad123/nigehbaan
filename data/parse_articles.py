#!/usr/bin/env python3
"""Parse all collected news articles into geocoded incident records.

Reads articles from data/raw/rss_monitor/, data/raw/dawn/, etc.
Runs them through the NewsArticleParser NLP pipeline.
Saves incident records to data/raw/incidents/.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import logging

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger("parse_articles")


def collect_articles() -> list[dict]:
    """Collect all articles from raw data directories."""
    articles: list[dict] = []
    raw_dir = ROOT / "data" / "raw"

    # RSS Monitor articles
    rss_dir = raw_dir / "rss_monitor"
    if rss_dir.exists():
        for f in sorted(rss_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        # Adapt: use 'summary' as 'full_text' for parser
                        item["full_text"] = item.get("full_text") or item.get("summary", "")
                        item["source"] = item.get("source", "rss_monitor")
                    articles.extend(data)
                    logger.info("Loaded %d articles from %s", len(data), f.name)
            except Exception as exc:
                logger.error("Error reading %s: %s", f, exc)

    # Dawn articles
    dawn_dir = raw_dir / "dawn"
    if dawn_dir.exists():
        for f in sorted(dawn_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        item["source"] = "dawn"
                    articles.extend(data)
                    logger.info("Loaded %d articles from %s", len(data), f.name)
            except Exception as exc:
                logger.error("Error reading %s: %s", f, exc)

    # Other news sources
    for source_dir_name in ["ary_news", "the_news", "tribune", "geo_news"]:
        source_dir = raw_dir / source_dir_name
        if source_dir.exists():
            for f in sorted(source_dir.glob("*.json"), reverse=True):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        for item in data:
                            item["source"] = source_dir_name
                        articles.extend(data)
                        logger.info("Loaded %d articles from %s/%s", len(data), source_dir_name, f.name)
                except Exception as exc:
                    logger.error("Error reading %s: %s", f, exc)

    logger.info("Total articles collected: %d", len(articles))
    return articles


def main() -> None:
    from data.parsers.news_article_parser import NewsArticleParser

    articles = collect_articles()
    if not articles:
        logger.warning("No articles found to parse")
        return

    parser = NewsArticleParser()
    logger.info("Parsing %d articles through NLP pipeline...", len(articles))
    incidents = parser.parse_batch(articles)

    # Filter: only keep incidents with a detected crime type
    real_incidents = [
        {**inc, "source": articles[i].get("source", "unknown")}
        for i, inc in enumerate(incidents)
        if inc.get("crime_type") and inc["crime_type"] != "other"
    ]

    logger.info(
        "Parsing complete: %d total → %d with detected crime type",
        len(incidents), len(real_incidents),
    )

    # Save to incidents directory
    output_dir = ROOT / "data" / "raw" / "incidents"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"news_incidents_{timestamp}.json"
    output_file.write_text(
        json.dumps(real_incidents, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("Saved %d incident records to %s", len(real_incidents), output_file)

    # Print summary
    from collections import Counter
    type_counts = Counter(inc["crime_type"] for inc in real_incidents)
    logger.info("Crime type breakdown:")
    for crime_type, count in type_counts.most_common():
        logger.info("  %s: %d", crime_type, count)

    geocoded = sum(1 for inc in real_incidents if inc.get("district_pcode"))
    logger.info("Geocoded: %d/%d (%.0f%%)", geocoded, len(real_incidents),
                100 * geocoded / max(len(real_incidents), 1))


if __name__ == "__main__":
    main()
