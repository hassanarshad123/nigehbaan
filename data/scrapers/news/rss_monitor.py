"""Multi-feed RSS monitor for trafficking-related news.

Monitors multiple RSS feeds simultaneously, including the Google News
RSS aggregator which provides a single feed of results from many
Pakistani news sources matching trafficking search terms.

Strategy:
    1. Maintain a registry of RSS feed URLs to monitor
    2. Fetch all feeds concurrently using asyncio
    3. Parse entries and extract article metadata
    4. Deduplicate entries across feeds by URL normalization
    5. Yield new (unseen) entries for downstream processing

Schedule: Every 4 hours (0 */4 * * *)
Priority: P1 — Aggregated monitoring across many sources
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import asyncio
import logging

import feedparser

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Default RSS feeds to monitor
DEFAULT_FEEDS: dict[str, str] = {
    "google_news_trafficking": (
        "https://news.google.com/rss/search?"
        "q=child+trafficking+Pakistan&hl=en-PK&gl=PK&ceid=PK:en"
    ),
    "google_news_child_abuse": (
        "https://news.google.com/rss/search?"
        "q=child+abuse+Pakistan&hl=en-PK&gl=PK&ceid=PK:en"
    ),
    "google_news_missing_children": (
        "https://news.google.com/rss/search?"
        "q=missing+children+Pakistan&hl=en-PK&gl=PK&ceid=PK:en"
    ),
    "dawn": "https://dawn.com/feeds/home",
    "tribune": "https://tribune.com.pk/feed",
    "the_news": "https://www.thenews.com.pk/rss",
    "ary_news": "https://arynews.tv/feed/",
}

# UTM and tracking parameters to strip during normalization
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_cid", "fbclid", "gclid", "gclsrc", "ref", "source",
    "ncid", "ocid", "_ga",
})


class RSSMonitor(BaseScraper):
    """Monitors multiple RSS feeds for trafficking-related articles.

    Acts as an aggregation layer that watches many feeds at once,
    deduplicates entries, and provides a unified stream of new
    articles for downstream processing.

    The Google News RSS aggregator is particularly valuable as it
    captures articles from sources we don't have dedicated scrapers
    for (Urdu-language outlets, regional papers, etc.).

    Attributes:
        name: Scraper identifier.
        source_url: Primary Google News aggregator URL.
        feeds: Dictionary mapping feed names to their URLs.
        seen_urls: Set of previously processed article URLs.
    """

    name: str = "rss_monitor"
    source_url: str = DEFAULT_FEEDS["google_news_trafficking"]
    schedule: str = "0 */4 * * *"
    priority: str = "P1"

    def __init__(self, feeds: dict[str, str] | None = None) -> None:
        super().__init__()
        self.feeds: dict[str, str] = feeds or dict(DEFAULT_FEEDS)
        self.seen_urls: set[str] = set()

    async def fetch_feed(self, name: str, url: str) -> list[dict[str, Any]]:
        """Fetch and parse a single RSS feed.

        Args:
            name: Identifier for this feed (for logging).
            url: RSS feed URL.

        Returns:
            List of parsed entry dicts with keys: title, url,
            published, summary, source_feed.
        """
        try:
            response = await self.fetch(url)
            xml_content = response.text
            parsed = await asyncio.to_thread(feedparser.parse, xml_content)

            if parsed.bozo and not parsed.entries:
                logger.warning(
                    "[%s] Feed '%s' returned malformed XML: %s",
                    self.name, name, parsed.bozo_exception,
                )
                return []

            entries = self.parse_entries(parsed.entries, name)
            logger.info(
                "[%s] Fetched %d entries from feed '%s'",
                self.name, len(entries), name,
            )
            return entries

        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch feed '%s' (%s): %s",
                self.name, name, url, exc,
            )
            return []

    def parse_entries(
        self, raw_entries: list[dict[str, Any]], source_feed: str
    ) -> list[dict[str, Any]]:
        """Parse raw feedparser entries into standardized format.

        Extracts and normalizes the key fields from each RSS entry
        into a consistent schema for downstream processing.

        Args:
            raw_entries: List of feedparser entry objects.
            source_feed: Name of the feed these entries came from.

        Returns:
            List of standardized entry dicts.
        """
        results: list[dict[str, Any]] = []

        for entry in raw_entries:
            link = entry.get("link", "")
            if not link:
                continue

            # Normalize for dedup (strip tracking params, etc.)
            # Note: Google News base64 path URLs (/rss/articles/CBMi...)
            # can't be resolved via HTTP (require JS). Titles and dates
            # are still extracted correctly from the RSS feed itself.
            normalized_link = self.normalize_url(link)

            # Parse published date
            published_date = self._parse_date(entry)

            # Extract summary, preferring plain text
            summary = ""
            if entry.get("summary"):
                summary = entry["summary"]
            elif entry.get("description"):
                summary = entry["description"]

            results.append({
                "title": entry.get("title", "").strip(),
                "url": normalized_link,
                "published_date": published_date,
                "summary": summary.strip(),
                "source_feed": source_feed,
                "source": self.name,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })

        return results

    @staticmethod
    def _parse_date(entry: dict[str, Any]) -> str:
        """Extract and normalize date from a feedparser entry to ISO format."""
        # feedparser provides parsed time tuples
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            try:
                dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (TypeError, ValueError):
                pass

        updated_parsed = entry.get("updated_parsed")
        if updated_parsed:
            try:
                dt = datetime(*updated_parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (TypeError, ValueError):
                pass

        # Fall back to raw string
        return entry.get("published", entry.get("updated", ""))

    def normalize_url(self, url: str) -> str:
        """Normalize a URL for deduplication.

        Strips query parameters, fragments, trailing slashes, and
        resolves Google News redirect URLs to their original source.

        Args:
            url: Raw URL from RSS feed entry.

        Returns:
            Normalized URL string for comparison.
        """
        if not url:
            return url

        # Handle Google News redirect URLs
        # Pattern: https://news.google.com/rss/articles/...
        # or https://news.google.com/articles/...
        parsed = urlparse(url)
        if "news.google.com" in parsed.netloc:
            # Google News URLs sometimes have the real URL in query params
            query_params = parse_qs(parsed.query)
            if "url" in query_params:
                url = query_params["url"][0]
                parsed = urlparse(url)

        # Strip tracking/UTM parameters
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        cleaned_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in _TRACKING_PARAMS
        }
        cleaned_query = urlencode(cleaned_params, doseq=True)

        # Reconstruct URL without fragment and with cleaned query
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/"),
            parsed.params,
            cleaned_query,
            "",  # strip fragment
        ))

        return normalized

    def deduplicate(
        self, entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Remove duplicate entries based on normalized URL.

        Also filters out entries that have been seen in previous
        runs (stored in self.seen_urls).

        Args:
            entries: List of entry dicts to deduplicate.

        Returns:
            List of unique, previously-unseen entries.
        """
        unique: list[dict[str, Any]] = []
        batch_seen: set[str] = set()

        for entry in entries:
            norm_url = self.normalize_url(entry.get("url", ""))
            if not norm_url:
                continue
            if norm_url in self.seen_urls or norm_url in batch_seen:
                continue
            batch_seen.add(norm_url)
            unique.append(entry)

        # Update persistent seen set with this batch
        self.seen_urls.update(batch_seen)

        logger.info(
            "[%s] Deduplicated %d entries down to %d new entries",
            self.name, len(entries), len(unique),
        )
        return unique

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the multi-feed RSS monitoring pipeline.

        Fetches all registered feeds concurrently, merges entries,
        deduplicates, and returns new articles.

        Returns:
            List of new, deduplicated article entries.
        """
        # 1. Fetch all feeds concurrently
        tasks = [
            self.fetch_feed(name, url)
            for name, url in self.feeds.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 2. Flatten all entries into a single list
        all_entries: list[dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                feed_name = list(self.feeds.keys())[i]
                logger.error(
                    "[%s] Feed '%s' raised exception: %s",
                    self.name, feed_name, result,
                )
                continue
            all_entries.extend(result)

        logger.info(
            "[%s] Collected %d total entries from %d feeds",
            self.name, len(all_entries), len(self.feeds),
        )

        # 3. Deduplicate across feeds and against seen_urls
        new_entries = self.deduplicate(all_entries)

        return new_entries

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an RSS entry record.

        Args:
            record: An RSS entry dictionary.

        Returns:
            True if required fields (url, title) are present.
        """
        required_fields = ["url", "title"]
        return all(record.get(f) for f in required_fields)
