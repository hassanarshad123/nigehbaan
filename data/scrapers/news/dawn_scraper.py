"""Dawn newspaper scraper for child trafficking and abuse articles.

Scrapes Dawn (dawn.com) via its RSS feed and article pages.
Dawn is Pakistan's oldest English-language newspaper with reliable
digital archives and well-structured HTML.

Strategy:
    1. Fetch RSS feed from dawn.com/feeds/home
    2. Parse feed entries for article URLs and metadata
    3. For each article, fetch full HTML and extract body text
    4. Filter articles matching trafficking/child abuse keyword list
    5. Store raw article data with metadata for downstream NER pipeline

Schedule: Every 6 hours (0 */6 * * *)
Priority: P1 — Core news source for incident detection
"""

from datetime import datetime, timezone
from typing import Any

import asyncio
import logging

import feedparser
from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Keywords used to filter relevant articles
TRAFFICKING_KEYWORDS: list[str] = [
    "child trafficking",
    "child abuse",
    "missing child",
    "kidnap",
    "abduct",
    "sexual abuse",
    "child labour",
    "child labor",
    "bonded labour",
    "brick kiln",
    "zina",
    "366-A",
    "370",
    "371",
    "FIA",
    "human trafficking",
    "child marriage",
    "minor girl", "minor boy", "minor victim", "minor age",
]


class DawnScraper(BaseScraper):
    """Scraper for Dawn newspaper articles related to child trafficking.

    Uses RSS feed as primary entry point, then fetches full article
    text via Scrapy-style HTTP requests. Dawn's HTML is clean and
    well-structured, making extraction reliable.

    Attributes:
        name: Scraper identifier.
        source_url: Dawn RSS feed URL.
        schedule: Cron expression for 6-hour intervals.
        priority: P1 core news source.
    """

    name: str = "dawn"
    source_url: str = "https://dawn.com/feeds/home"
    schedule: str = "0 */6 * * *"
    priority: str = "P1"

    def __init__(self) -> None:
        super().__init__()
        self.keywords: list[str] = TRAFFICKING_KEYWORDS

    async def fetch_rss(self) -> list[dict[str, Any]]:
        """Fetch and parse the Dawn RSS feed.

        Returns:
            List of feed entries with title, link, published date,
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

            logger.info(
                "[%s] Fetched %d RSS entries", self.name, len(entries),
            )
            return entries

        except Exception as exc:
            logger.error("[%s] Failed to fetch RSS: %s", self.name, exc)
            return []

    async def fetch_article(self, url: str) -> dict[str, Any]:
        """Fetch full article content from a Dawn article URL.

        Args:
            url: Full URL to the Dawn article page.

        Returns:
            Dictionary with keys: url, title, author, published_date,
            full_text, section, tags.
        """
        try:
            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title from h2.story__title or og:title
            title = ""
            title_tag = soup.find("h2", class_="story__title")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    title = og_title.get("content", "")

            # Extract article body from div.story__content
            full_text = ""
            content_div = soup.find("div", class_="story__content")
            if content_div:
                paragraphs = content_div.find_all("p")
                full_text = "\n\n".join(
                    p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
                )

            # Extract author from span.story__byline
            author = ""
            byline = soup.find("span", class_="story__byline")
            if byline:
                # Remove "By" prefix and clean up
                author_link = byline.find("a")
                if author_link:
                    author = author_link.get_text(strip=True)
                else:
                    author = byline.get_text(strip=True)
                author = author.removeprefix("By").strip()

            # Extract published date from time tag
            published_date = ""
            time_tag = soup.find("time")
            if time_tag:
                published_date = time_tag.get("datetime", "")
                if not published_date:
                    published_date = time_tag.get_text(strip=True)

            # Extract tags from article metadata
            tags: list[str] = []
            tag_elements = soup.find_all("a", class_="story__tag")
            for tag_el in tag_elements:
                tag_text = tag_el.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)

            # Extract section/category
            section = ""
            breadcrumb = soup.find("ul", class_="breadcrumb")
            if breadcrumb:
                crumb_links = breadcrumb.find_all("a")
                if len(crumb_links) > 1:
                    section = crumb_links[-1].get_text(strip=True)

            return {
                "url": url,
                "title": title,
                "author": author,
                "published_date": published_date,
                "full_text": full_text,
                "source": self.name,
                "section": section,
                "tags": tags,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch article %s: %s", self.name, url, exc,
            )
            return {}

    def matches_keywords(self, text: str) -> bool:
        """Check if article text contains any trafficking-related keywords.

        Args:
            text: Combined title + body text of the article.

        Returns:
            True if any keyword is found (case-insensitive).
        """
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.keywords)

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the Dawn scraping pipeline.

        Fetches RSS feed, retrieves full articles for each entry,
        filters by keyword relevance, and returns matching records.

        Returns:
            List of article records matching trafficking keywords.
        """
        # 1. Fetch RSS feed entries
        rss_entries = await self.fetch_rss()
        if not rss_entries:
            logger.warning("[%s] No RSS entries found", self.name)
            return []

        # 2. Fetch full articles concurrently (with concurrency limit)
        semaphore = asyncio.Semaphore(5)

        async def _fetch_with_limit(entry: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                article = await self.fetch_article(entry["url"])
                # Merge RSS metadata if article fetch failed to get them
                if article:
                    if not article.get("title") and entry.get("title"):
                        article["title"] = entry["title"]
                    if not article.get("published_date") and entry.get("published_date"):
                        article["published_date"] = entry["published_date"]
                return article

        tasks = [_fetch_with_limit(entry) for entry in rss_entries]
        articles = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Filter by keywords
        matching: list[dict[str, Any]] = []
        for result in articles:
            if isinstance(result, Exception):
                logger.error("[%s] Article fetch error: %s", self.name, result)
                continue
            if not result or not result.get("url"):
                continue

            combined_text = f"{result.get('title', '')} {result.get('full_text', '')}"
            if self.matches_keywords(combined_text):
                matching.append(result)

        logger.info(
            "[%s] Found %d matching articles out of %d total",
            self.name, len(matching), len(rss_entries),
        )
        return matching

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a scraped Dawn article record.

        Checks that required fields are present and non-empty:
        url, title, published_date, full_text.

        Args:
            record: A scraped article dictionary.

        Returns:
            True if all required fields are present and valid.
        """
        required_fields = ["url", "title", "published_date", "full_text"]
        return all(record.get(f) for f in required_fields)
