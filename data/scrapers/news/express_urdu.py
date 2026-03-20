"""Express Urdu news scraper for child trafficking and abuse articles.

Scrapes Daily Express (express.pk), a major Urdu-language newspaper
in Pakistan. Fetches the latest news listing page, extracts article
links, fetches each article's full text, and filters by Urdu
trafficking keywords.

Source: https://www.express.pk/latest-news/
Schedule: Every 6 hours (0 */6 * * *)
Priority: P1 — Core Urdu news source for incident detection
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncio
import json
import logging

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


class ExpressUrduScraper(BaseScraper):
    """Scraper for Daily Express Urdu newspaper articles.

    Targets the latest-news listing page, extracts article URLs,
    fetches full article text in Urdu, and filters for child
    trafficking and abuse-related content using Urdu keywords.

    Attributes:
        name: Scraper identifier.
        source_url: Express Urdu latest news URL.
        schedule: Cron expression for 6-hour intervals.
        priority: P1 core Urdu news source.
    """

    name: str = "express_urdu"
    source_url: str = "https://www.express.pk/latest-news/"
    schedule: str = "0 */6 * * *"
    priority: str = "P1"

    rate_limit_delay: float = 1.5

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

    async def _fetch_article_links(self) -> list[str]:
        """Fetch the listing page and extract article URLs.

        Returns:
            List of absolute article URLs from the listing page.
        """
        try:
            response = await self.fetch(self.source_url)
            soup = BeautifulSoup(response.text, "html.parser")

            links: list[str] = []
            # Express uses heading links and list structures for articles
            for selector in ["h2 a", "h3 a", ".listing-page a", ".entry-title a", "a.td-image-wrap"]:
                for anchor in soup.select(selector):
                    href = anchor.get("href", "")
                    if not href or href == "#":
                        continue
                    if href.startswith("/"):
                        href = f"https://www.express.pk{href}"
                    if "express.pk" in href and href not in links:
                        links.append(href)

            # Fallback: grab links that look like article URLs
            if not links:
                for anchor in soup.find_all("a", href=True):
                    href = anchor["href"]
                    if "express.pk" in href and "/story/" in href:
                        if href not in links:
                            links.append(href)

            logger.info("[%s] Found %d article links", self.name, len(links))
            return links

        except Exception as exc:
            logger.error("[%s] Failed to fetch listing page: %s", self.name, exc)
            return []

    async def _fetch_article(self, url: str) -> dict[str, Any]:
        """Fetch and parse a single Express Urdu article.

        Args:
            url: Full URL to the article page.

        Returns:
            Article record dict with standard fields.
        """
        try:
            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = ""
            title_tag = soup.find("h1", class_="entry-title") or soup.find("h1")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    title = og_title.get("content", "")

            # Extract body text
            full_text = ""
            body_div = (
                soup.find("div", class_="entry-content")
                or soup.find("div", class_="td-post-content")
                or soup.find("article")
            )
            if body_div:
                paragraphs = body_div.find_all("p")
                full_text = "\n\n".join(
                    p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
                )

            # Extract author
            author = ""
            author_tag = (
                soup.find("a", class_="author-name")
                or soup.find("span", class_="td-post-author-name")
            )
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
        """Execute the Express Urdu scraping pipeline.

        Steps:
            1. Fetch listing page and extract article links.
            2. Fetch full article content concurrently.
            3. Filter articles matching Urdu keywords.

        Returns:
            List of article records matching trafficking keywords.
        """
        article_urls = await self._fetch_article_links()
        if not article_urls:
            logger.warning("[%s] No article links found", self.name)
            return []

        # Fetch articles concurrently with concurrency limit
        semaphore = asyncio.Semaphore(5)

        async def _fetch_limited(url: str) -> dict[str, Any]:
            async with semaphore:
                return await self._fetch_article(url)

        tasks = [_fetch_limited(url) for url in article_urls]
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
            "[%s] Found %d matching articles out of %d fetched",
            self.name, len(matching), len(article_urls),
        )
        return matching

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a scraped Express Urdu article record.

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
