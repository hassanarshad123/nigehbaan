"""The News International scraper for child trafficking articles.

Scrapes The News International (thenews.com.pk) via RSS feed.
The News is part of the Jang Group and provides English-language
coverage across Pakistan with good digital archives.

Strategy:
    1. Fetch RSS feed from thenews.com.pk
    2. Parse feed entries for article URLs
    3. Fetch full article HTML and extract body text
    4. Filter by trafficking/child abuse keyword list
    5. Standardize output schema for downstream pipeline

Schedule: Every 6 hours (0 */6 * * *)
Priority: P1 — Major English-language daily
"""

from datetime import datetime, timezone
from typing import Any

import asyncio
import logging
import re

import feedparser
from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TheNewsScraper(BaseScraper):
    """Scraper for The News International articles on child trafficking.

    The News provides an RSS feed that can be monitored for new articles.
    Article pages have relatively clean HTML structure suitable for
    BeautifulSoup extraction.

    Attributes:
        name: Scraper identifier.
        source_url: The News RSS feed URL.
        schedule: Cron expression for 6-hour intervals.
        priority: P1 core news source.
    """

    name: str = "the_news"
    source_url: str = "https://www.thenews.com.pk/rss"
    schedule: str = "0 */6 * * *"
    priority: str = "P1"

    RSS_URLS: list[str] = [
        "https://www.thenews.com.pk/rss",
        "https://www.thenews.com.pk/rss/1/1",
        "https://www.thenews.com.pk/rss/1/7",  # national
        "https://www.thenews.com.pk/rss/1/2",  # pakistan
    ]

    GOOGLE_NEWS_FALLBACK: str = (
        "https://news.google.com/rss/search?"
        "q=site:thenews.com.pk+child+trafficking&hl=en-PK&gl=PK&ceid=PK:en"
    )

    @staticmethod
    def _sanitize_xml(text: str) -> str:
        """Strip invalid XML control characters that break feedparser."""
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    async def fetch_rss(self) -> list[dict[str, Any]]:
        """Fetch and parse The News International RSS feed.

        Tries multiple RSS endpoints sequentially until one yields entries.

        Returns:
            List of feed entry dicts with title, link, published, summary.
        """
        entries: list[dict[str, Any]] = []

        for rss_url in self.RSS_URLS:
            try:
                response = await self.fetch(rss_url)
                sanitized = self._sanitize_xml(response.text)
                parsed = await asyncio.to_thread(feedparser.parse, sanitized)

                if parsed.bozo and not parsed.entries:
                    logger.warning(
                        "[%s] RSS feed malformed at %s: %s",
                        self.name, rss_url, parsed.bozo_exception,
                    )
                    continue

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

                if entries:
                    logger.info(
                        "[%s] Fetched %d RSS entries from %s",
                        self.name, len(entries), rss_url,
                    )
                    return entries

            except Exception as exc:
                logger.warning("[%s] RSS fetch failed for %s: %s", self.name, rss_url, exc)
                continue

        logger.warning("[%s] All RSS endpoints failed", self.name)
        return entries

    async def fetch_article(self, url: str) -> dict[str, Any]:
        """Fetch full article content from The News article URL.

        Args:
            url: Full URL to the article page.

        Returns:
            Dictionary with url, title, author, published_date,
            full_text, section.
        """
        try:
            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = ""
            title_tag = soup.find("h1")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    title = og_title.get("content", "")

            # Extract article body — The News uses several content div patterns
            full_text = ""
            content_selectors = [
                ("div", {"class": "detail-content"}),
                ("div", {"class": "article-content"}),
                ("div", {"class": "story-detail"}),
                ("div", {"class": "detail-desc"}),
                ("div", {"id": "article-detail"}),
            ]
            for tag_name, attrs in content_selectors:
                content_div = soup.find(tag_name, attrs)
                if content_div:
                    paragraphs = content_div.find_all("p")
                    full_text = "\n\n".join(
                        p.get_text(strip=True)
                        for p in paragraphs
                        if p.get_text(strip=True)
                    )
                    if full_text:
                        break

            # Fallback: try print-friendly version structure
            if not full_text:
                article_body = soup.find("div", class_="col-md-8") or soup.find("article")
                if article_body:
                    paragraphs = article_body.find_all("p")
                    full_text = "\n\n".join(
                        p.get_text(strip=True)
                        for p in paragraphs
                        if p.get_text(strip=True)
                    )

            # Extract author
            author = ""
            author_selectors = [
                ("span", {"class": "detail-writer"}),
                ("a", {"class": "story-author"}),
                ("span", {"class": "author-name"}),
                ("a", {"rel": "author"}),
            ]
            for tag_name, attrs in author_selectors:
                author_tag = soup.find(tag_name, attrs)
                if author_tag:
                    author = author_tag.get_text(strip=True)
                    break

            # Fallback: look in meta tags
            if not author:
                author_meta = soup.find("meta", attrs={"name": "author"})
                if author_meta:
                    author = author_meta.get("content", "")

            # Extract published date
            published_date = ""
            time_tag = soup.find("time")
            if time_tag:
                published_date = time_tag.get("datetime", "")
                if not published_date:
                    published_date = time_tag.get_text(strip=True)
            if not published_date:
                date_meta = soup.find("meta", property="article:published_time")
                if date_meta:
                    published_date = date_meta.get("content", "")
            if not published_date:
                date_span = soup.find("span", class_="detail-time") or soup.find(
                    "span", class_="story-date"
                )
                if date_span:
                    published_date = date_span.get_text(strip=True)

            # Extract section
            section = ""
            section_tag = soup.find("a", class_="category-name") or soup.find(
                "span", class_="detail-category"
            )
            if section_tag:
                section = section_tag.get_text(strip=True)
            if not section:
                breadcrumb = soup.find("ol", class_="breadcrumb") or soup.find(
                    "ul", class_="breadcrumb"
                )
                if breadcrumb:
                    crumbs = breadcrumb.find_all("a")
                    if len(crumbs) > 1:
                        section = crumbs[-1].get_text(strip=True)

            return {
                "url": url,
                "title": title,
                "author": author,
                "published_date": published_date,
                "full_text": full_text,
                "source": self.name,
                "section": section,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch article %s: %s", self.name, url, exc,
            )
            return {}

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute The News scraping pipeline.

        Fetches RSS feed, retrieves full articles, filters by
        keyword relevance, and returns matching records.

        Returns:
            List of article records matching trafficking keywords.
        """
        # 1. Fetch RSS feed entries
        rss_entries = await self.fetch_rss()

        # Google News fallback if no RSS entries
        if not rss_entries:
            logger.info("[%s] No RSS entries, trying Google News fallback", self.name)
            try:
                response = await self.fetch(self.GOOGLE_NEWS_FALLBACK)
                sanitized = self._sanitize_xml(response.text)
                gn_parsed = await asyncio.to_thread(feedparser.parse, sanitized)
                for entry in gn_parsed.entries:
                    link = entry.get("link", "")
                    if link and "thenews.com.pk" in link:
                        rss_entries.append({
                            "title": entry.get("title", "").strip(),
                            "url": link.strip(),
                            "published_date": entry.get("published", ""),
                        })
                logger.info(
                    "[%s] Google News fallback yielded %d entries",
                    self.name, len(rss_entries),
                )
            except Exception as exc:
                logger.error("[%s] Google News fallback failed: %s", self.name, exc)

        if not rss_entries:
            logger.warning("[%s] No entries found from any source", self.name)
            return []

        # 2. Fetch full articles with concurrency limit
        semaphore = asyncio.Semaphore(5)

        async def _fetch_with_limit(entry: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                article = await self.fetch_article(entry["url"])
                if article:
                    # Merge RSS metadata as fallback
                    if not article.get("title") and entry.get("title"):
                        article["title"] = entry["title"]
                    if not article.get("published_date") and entry.get("published_date"):
                        article["published_date"] = entry["published_date"]
                return article

        tasks = [_fetch_with_limit(entry) for entry in rss_entries]
        articles = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Filter by trafficking keywords
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
        """Validate a scraped The News article record.

        Args:
            record: A scraped article dictionary.

        Returns:
            True if required fields are present and valid.
        """
        required_fields = ["url", "title", "published_date", "full_text"]
        return all(record.get(f) for f in required_fields)
