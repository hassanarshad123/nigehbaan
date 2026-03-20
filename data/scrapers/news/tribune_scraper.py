"""Express Tribune scraper for child trafficking and abuse articles.

Scrapes Express Tribune (tribune.com.pk) via WordPress RSS feed
and dedicated tag pages. Tribune has a WordPress-based CMS with
accessible RSS feeds and a dedicated child-trafficking tag page.

Strategy:
    1. Fetch WordPress RSS feed for latest articles
    2. Additionally scrape the dedicated tag page:
       tribune.com.pk/child-trafficking/
    3. Parse article metadata and full text
    4. Filter for trafficking/abuse keywords
    5. Deduplicate against previously seen URLs

Schedule: Every 6 hours (0 */6 * * *)
Priority: P1 — Major English-language newspaper
"""

from datetime import datetime, timezone
from typing import Any

import asyncio
import logging

import feedparser
from bs4 import BeautifulSoup

import httpx

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Browser-like headers to avoid Tribune's WAF blocking
_TRIBUNE_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://tribune.com.pk/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Maximum number of tag pages to scrape per run
MAX_TAG_PAGES = 3


class TribuneScraper(BaseScraper):
    """Scraper for Express Tribune articles on child trafficking.

    Uses two entry points: the WordPress RSS feed for general articles
    and the dedicated child-trafficking tag page for targeted content.
    Tribune's WordPress structure provides clean, predictable HTML.

    Attributes:
        name: Scraper identifier.
        source_url: Tribune RSS feed URL.
        tag_page_url: Dedicated trafficking tag page.
        schedule: Cron expression for 6-hour intervals.
        priority: P1 core news source.
    """

    name: str = "tribune"
    source_url: str = "https://tribune.com.pk/feed"
    tag_page_url: str = "https://tribune.com.pk/child-trafficking/"
    schedule: str = "0 */6 * * *"
    priority: str = "P1"
    max_retries: int = 1  # Tribune 403s are permanent, don't waste time retrying

    async def get_client(self) -> httpx.AsyncClient:
        """Override to use browser-like headers for all Tribune requests."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.request_timeout),
                follow_redirects=True,
                headers=_TRIBUNE_HEADERS,
            )
        return self._client

    async def fetch_rss(self) -> list[dict[str, Any]]:
        """Fetch and parse the Express Tribune WordPress RSS feed.

        Returns:
            List of feed entry dicts with title, link, published, summary.
        """
        try:
            response = await self.fetch(self.source_url)
            parsed = await asyncio.to_thread(feedparser.parse, response.text)

            if parsed.bozo and not parsed.entries:
                logger.warning(
                    "[%s] RSS feed malformed: %s",
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

                # Extract WordPress dc:creator if present
                author = entry.get("author", "")
                if not author:
                    author = entry.get("dc_creator", "")

                # Extract categories/tags from WordPress feed
                tags: list[str] = []
                for tag_info in entry.get("tags", []):
                    tag_term = tag_info.get("term", "")
                    if tag_term:
                        tags.append(tag_term)

                entries.append({
                    "title": entry.get("title", "").strip(),
                    "url": link.strip(),
                    "published_date": published,
                    "summary": entry.get("summary", "").strip(),
                    "author": author.strip(),
                    "tags": tags,
                })

            logger.info(
                "[%s] Fetched %d RSS entries", self.name, len(entries),
            )
            return entries

        except Exception as exc:
            logger.error("[%s] Failed to fetch RSS: %s", self.name, exc)
            return []

    async def fetch_tag_page(self, page: int = 1) -> list[dict[str, Any]]:
        """Scrape the child-trafficking tag page for article links.

        The tag page lists articles specifically tagged with
        child-trafficking, providing higher-precision results than
        the general RSS feed.

        Args:
            page: Pagination page number (Tribune uses /page/N/).

        Returns:
            List of article stub dicts with url and title.
        """
        url = self.tag_page_url
        if page > 1:
            url = f"{self.tag_page_url}page/{page}/"

        try:
            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, "html.parser")

            entries: list[dict[str, Any]] = []

            # Tribune tag pages list article cards/links
            # Try common WordPress theme patterns
            article_elements = soup.find_all("article")
            if not article_elements:
                # Fallback: look for heading links in content area
                article_elements = soup.find_all("div", class_="listing-page")

            for article_el in article_elements:
                # Find the primary heading link
                heading = article_el.find(["h2", "h3", "h4"])
                if not heading:
                    continue

                link_tag = heading.find("a")
                if not link_tag:
                    continue

                article_url = link_tag.get("href", "")
                title = link_tag.get_text(strip=True)

                if not article_url or not title:
                    continue

                # Ensure absolute URL
                if article_url.startswith("/"):
                    article_url = f"https://tribune.com.pk{article_url}"

                entries.append({
                    "url": article_url,
                    "title": title,
                })

            # Fallback: scan entire page for Tribune story links
            if not entries:
                seen_hrefs: set[str] = set()
                for link_tag in soup.find_all("a", href=True):
                    href = link_tag.get("href", "")
                    text = link_tag.get_text(strip=True)
                    if (
                        href
                        and text
                        and len(text) > 20
                        and "/story/" in href
                        and href not in seen_hrefs
                    ):
                        # Ensure absolute URL
                        if href.startswith("/"):
                            href = f"https://tribune.com.pk{href}"
                        seen_hrefs.add(href)
                        entries.append({"url": href, "title": text})

            logger.info(
                "[%s] Found %d entries on tag page %d",
                self.name, len(entries), page,
            )
            return entries

        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch tag page %d: %s",
                self.name, page, exc,
            )
            return []

    async def fetch_article(self, url: str) -> dict[str, Any]:
        """Fetch full article content from a Tribune article URL.

        Args:
            url: Full URL to the Tribune article page.

        Returns:
            Dictionary with url, title, author, published_date,
            full_text, category, tags.
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

            # Extract article body — Tribune uses <span class="story-text"> for content
            full_text = ""
            # Primary: collect paragraphs from story-text spans
            story_text_spans = soup.find_all("span", class_="story-text")
            if story_text_spans:
                paragraphs = []
                for span in story_text_spans:
                    paragraphs.extend(span.find_all("p"))
                full_text = "\n\n".join(
                    p.get_text(strip=True)
                    for p in paragraphs
                    if p.get_text(strip=True)
                )

            # Fallback: main content container
            if not full_text:
                content_selectors = [
                    ("div", {"class": "storypage"}),
                    ("div", {"class": "story-description"}),
                    ("div", {"class": "entry-content"}),
                    ("article", {}),
                ]
                for tag_name, attrs in content_selectors:
                    content_div = soup.find(tag_name, attrs) if attrs else soup.find(tag_name)
                    if content_div:
                        paragraphs = content_div.find_all("p")
                        full_text = "\n\n".join(
                            p.get_text(strip=True)
                            for p in paragraphs
                            if p.get_text(strip=True)
                        )
                        if full_text:
                            break

            # Extract author
            author = ""
            author_selectors = [
                ("span", {"class": "story-author"}),
                ("a", {"class": "author-name"}),
                ("span", {"class": "author"}),
                ("a", {"rel": "author"}),
            ]
            for tag_name, attrs in author_selectors:
                author_tag = soup.find(tag_name, attrs)
                if author_tag:
                    author = author_tag.get_text(strip=True)
                    break

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

            # Extract category
            category = ""
            cat_tag = soup.find("a", class_="category-name") or soup.find(
                "span", class_="story-cat"
            )
            if cat_tag:
                category = cat_tag.get_text(strip=True)

            # Extract tags
            tags: list[str] = []
            tag_container = soup.find("div", class_="story-tags") or soup.find(
                "div", class_="tags"
            )
            if tag_container:
                for a_tag in tag_container.find_all("a"):
                    tag_text = a_tag.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)

            return {
                "url": url,
                "title": title,
                "author": author,
                "published_date": published_date,
                "full_text": full_text,
                "source": self.name,
                "category": category,
                "tags": tags,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch article %s: %s", self.name, url, exc,
            )
            return {}

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the Tribune scraping pipeline.

        Combines results from RSS feed and tag page, deduplicates
        by URL, fetches full articles, and filters by relevance.

        Returns:
            List of article records matching trafficking keywords.
        """
        # 1. Fetch RSS entries and tag page entries concurrently
        rss_task = self.fetch_rss()
        tag_tasks = [self.fetch_tag_page(page) for page in range(1, MAX_TAG_PAGES + 1)]

        rss_entries, *tag_results = await asyncio.gather(
            rss_task, *tag_tasks, return_exceptions=True,
        )

        # Collect all article stubs
        all_stubs: list[dict[str, Any]] = []

        if isinstance(rss_entries, list):
            all_stubs.extend(rss_entries)
        elif isinstance(rss_entries, Exception):
            logger.error("[%s] RSS fetch error: %s", self.name, rss_entries)

        for result in tag_results:
            if isinstance(result, list):
                all_stubs.extend(result)
            elif isinstance(result, Exception):
                logger.error("[%s] Tag page error: %s", self.name, result)

        if not all_stubs:
            logger.warning("[%s] No article stubs found", self.name)
            return []

        # 2. Deduplicate by URL
        seen_urls: set[str] = set()
        unique_stubs: list[dict[str, Any]] = []
        for stub in all_stubs:
            url = stub.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_stubs.append(stub)

        logger.info(
            "[%s] %d unique articles after dedup (from %d total)",
            self.name, len(unique_stubs), len(all_stubs),
        )

        # 3. Fetch full articles with concurrency limit
        semaphore = asyncio.Semaphore(5)

        async def _fetch_with_limit(stub: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                article = await self.fetch_article(stub["url"])
                if article:
                    # Merge stub metadata if article extraction missed fields
                    if not article.get("title") and stub.get("title"):
                        article["title"] = stub["title"]
                    if not article.get("published_date") and stub.get("published_date"):
                        article["published_date"] = stub["published_date"]
                    if not article.get("author") and stub.get("author"):
                        article["author"] = stub["author"]
                return article

        tasks = [_fetch_with_limit(stub) for stub in unique_stubs]
        articles = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. Filter by keywords
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
            "[%s] Found %d matching articles out of %d unique",
            self.name, len(matching), len(unique_stubs),
        )
        return matching

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a scraped Tribune article record.

        Args:
            record: A scraped article dictionary.

        Returns:
            True if required fields (url, title, published_date,
            full_text) are present.
        """
        required_fields = ["url", "title", "published_date", "full_text"]
        return all(record.get(f) for f in required_fields)
