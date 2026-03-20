"""BBC Urdu news scraper for child trafficking and abuse articles.

Scrapes BBC Urdu via its RSS feed, following the same RSS-first pattern
as the DawnScraper. BBC Urdu provides high-quality Urdu journalism
with well-structured HTML and a reliable RSS feed.

Source: https://feeds.bbci.co.uk/urdu/rss.xml
Schedule: Every 6 hours (0 */6 * * *)
Priority: P1 — Core Urdu news source for incident detection
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncio
import json
import logging

import feedparser
from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


def _load_urdu_keywords() -> list[str]:
    """Load Urdu keyword list from the config file.

    Returns:
        List of Urdu keyword strings, or empty list if config is missing.
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "urdu_keywords.json"
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return data.get("urdu_only", [])
    return []


class BBCUrduScraper(BaseScraper):
    """Scraper for BBC Urdu news articles via RSS feed.

    Uses the BBC Urdu RSS feed as the primary entry point, then
    fetches full article text from BBC Urdu web pages. Filters
    articles using Urdu trafficking and child abuse keywords.

    Attributes:
        name: Scraper identifier.
        source_url: BBC Urdu RSS feed URL.
        schedule: Cron expression for 6-hour intervals.
        priority: P1 core Urdu news source.
    """

    name: str = "bbc_urdu"
    source_url: str = "https://feeds.bbci.co.uk/urdu/rss.xml"
    schedule: str = "0 */6 * * *"
    priority: str = "P1"

    rate_limit_delay: float = 1.0

    def __init__(self) -> None:
        super().__init__()
        self.urdu_keywords: list[str] = _load_urdu_keywords()

    def _matches_urdu_keywords(self, text: str) -> bool:
        """Check if text contains any Urdu trafficking keywords.

        Args:
            text: Combined title + body text.

        Returns:
            True if any Urdu keyword is found.
        """
        return any(kw in text for kw in self.urdu_keywords)

    async def fetch_rss(self) -> list[dict[str, Any]]:
        """Fetch and parse the BBC Urdu RSS feed.

        Returns:
            List of feed entries with title, url, published_date,
            and summary fields.
        """
        try:
            response = await self.fetch(self.source_url)
            parsed = await asyncio.to_thread(feedparser.parse, response.text)

            if parsed.bozo and not parsed.entries:
                logger.warning(
                    "[%s] RSS feed returned malformed XML: %s",
                    self.name, parsed.bozo_exception,
                )
                return []

            entries: list[dict[str, Any]] = []
            for entry in parsed.entries:
                link = entry.get("link", "")
                if not link:
                    continue

                published = ""
                if entry.get("published_parsed"):
                    try:
                        dt = datetime(
                            *entry["published_parsed"][:6],
                            tzinfo=timezone.utc,
                        )
                        published = dt.isoformat()
                    except (TypeError, ValueError):
                        published = entry.get("published", "")

                entries.append({
                    "title": entry.get("title", "").strip(),
                    "url": link.strip(),
                    "published_date": published,
                    "summary": entry.get("summary", "").strip(),
                })

            logger.info("[%s] Fetched %d RSS entries", self.name, len(entries))
            return entries

        except Exception as exc:
            logger.error("[%s] Failed to fetch RSS: %s", self.name, exc)
            return []

    async def fetch_article(self, url: str) -> dict[str, Any]:
        """Fetch full article content from a BBC Urdu article URL.

        Args:
            url: Full URL to the BBC Urdu article page.

        Returns:
            Dictionary with standard article fields.
        """
        try:
            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title from h1 or og:title
            title = ""
            title_tag = soup.find("h1")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    title = og_title.get("content", "")

            # Extract article body
            full_text = ""
            # BBC Urdu uses various article body containers
            body_div = (
                soup.find("main", role="main")
                or soup.find("div", attrs={"data-component": "text-block"})
                or soup.find("article")
            )
            if body_div:
                paragraphs = body_div.find_all("p")
                full_text = "\n\n".join(
                    p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
                )
            else:
                # Fallback: collect all paragraphs from the page
                all_paras = soup.find_all("p")
                full_text = "\n\n".join(
                    p.get_text(strip=True) for p in all_paras
                    if p.get_text(strip=True) and len(p.get_text(strip=True)) > 30
                )

            # Extract author
            author = ""
            author_tag = soup.find("div", class_=lambda c: c and "byline" in c.lower() if c else False)
            if author_tag:
                author = author_tag.get_text(strip=True)

            # Extract published date
            published_date = ""
            time_tag = soup.find("time")
            if time_tag:
                published_date = time_tag.get("datetime", time_tag.get_text(strip=True))
            else:
                date_meta = soup.find("meta", property="article:published_time")
                if date_meta:
                    published_date = date_meta.get("content", "")

            return {
                "url": url,
                "title": title,
                "published_date": published_date,
                "full_text": full_text,
                "source": self.name,
                "author": author,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            logger.error("[%s] Failed to fetch article %s: %s", self.name, url, exc)
            return {}

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the BBC Urdu scraping pipeline.

        Steps:
            1. Fetch RSS feed entries.
            2. Fetch full article content for each entry concurrently.
            3. Filter articles matching Urdu trafficking keywords.

        Returns:
            List of article records matching trafficking keywords.
        """
        rss_entries = await self.fetch_rss()
        if not rss_entries:
            logger.warning("[%s] No RSS entries found", self.name)
            return []

        # Fetch articles concurrently with concurrency limit
        semaphore = asyncio.Semaphore(5)

        async def _fetch_with_limit(entry: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                article = await self.fetch_article(entry["url"])
                # Merge RSS metadata if article fetch missed them
                if article:
                    if not article.get("title") and entry.get("title"):
                        article["title"] = entry["title"]
                    if not article.get("published_date") and entry.get("published_date"):
                        article["published_date"] = entry["published_date"]
                return article

        tasks = [_fetch_with_limit(entry) for entry in rss_entries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter by Urdu keywords
        matching: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("[%s] Article fetch error: %s", self.name, result)
                continue
            if not result or not result.get("url"):
                continue

            combined_text = f"{result.get('title', '')} {result.get('full_text', '')}"
            if self._matches_urdu_keywords(combined_text):
                matching.append(result)

        logger.info(
            "[%s] Found %d matching articles out of %d total",
            self.name, len(matching), len(rss_entries),
        )
        return matching

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a scraped BBC Urdu article record.

        Requires url, title, and full_text to be present and non-empty.

        Args:
            record: A scraped article dictionary.

        Returns:
            True if required fields are present and valid.
        """
        return bool(
            record.get("url")
            and record.get("title")
            and record.get("full_text")
        )
