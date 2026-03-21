"""ARY News scraper for child trafficking and abuse articles.

Scrapes ARY News (arynews.tv) via its WordPress RSS feed.
ARY is one of Pakistan's largest private TV news networks with
a WordPress-based website providing structured RSS feeds.

Strategy:
    1. Fetch WordPress RSS feed from arynews.tv/feed
    2. Parse feed entries for article URLs and metadata
    3. Fetch full article HTML from WordPress content
    4. Filter articles matching trafficking/abuse keywords
    5. Extract additional metadata from WordPress taxonomy

Schedule: Every 6 hours (0 */6 * * *)
Priority: P1 — Major TV news network with active web presence
"""

from datetime import datetime, timezone
from typing import Any

import asyncio
import logging

import feedparser
from bs4 import BeautifulSoup

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Search terms used for WordPress API queries
WP_API_SEARCH_TERMS: list[str] = [
    "child trafficking",
    "child abuse",
    "missing children",
    "kidnapping children",
    "human trafficking",
    "rape",
    "kidnap",
    "missing child",
    "sodomy",
    "child labour",
    "trafficking",
]

_GOOGLE_NEWS_ARY_FALLBACK = (
    "https://news.google.com/rss/search?"
    "q=site:arynews.tv+child+trafficking&hl=en-PK&gl=PK&ceid=PK:en"
)


class ARYScraper(BaseScraper):
    """Scraper for ARY News articles on child trafficking.

    ARY News uses WordPress, providing reliable RSS feeds and
    predictable HTML structure. The WordPress REST API may also
    be available as an alternative extraction method.

    Attributes:
        name: Scraper identifier.
        source_url: ARY News WordPress RSS feed URL.
        schedule: Cron expression for 6-hour intervals.
        priority: P1 core news source.
    """

    name: str = "ary_news"
    source_url: str = "https://arynews.tv/feed/"
    schedule: str = "0 */6 * * *"
    priority: str = "P1"

    GOOGLE_NEWS_FALLBACK: str = (
        "https://news.google.com/rss/search?"
        "q=site:arynews.tv+child+trafficking&hl=en-PK&gl=PK&ceid=PK:en"
    )

    async def fetch_rss(self) -> list[dict[str, Any]]:
        """Fetch and parse the ARY News WordPress RSS feed.

        Returns:
            List of feed entry dicts with title, link, published,
            summary, and WordPress category/tag metadata.
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

                # WordPress dc:creator field
                author = entry.get("author", "")
                if not author:
                    author = entry.get("dc_creator", "")

                # WordPress categories and tags
                categories: list[str] = []
                tags: list[str] = []
                for tag_info in entry.get("tags", []):
                    term = tag_info.get("term", "")
                    scheme = tag_info.get("scheme") or ""
                    if not term:
                        continue
                    if "category" in scheme.lower():
                        categories.append(term)
                    else:
                        tags.append(term)
                    # If no scheme, add to tags
                    if not scheme:
                        tags.append(term)

                entries.append({
                    "title": entry.get("title", "").strip(),
                    "url": link.strip(),
                    "published_date": published,
                    "summary": entry.get("summary", "").strip(),
                    "author": author.strip(),
                    "category": ", ".join(categories) if categories else "",
                    "tags": tags,
                })

            logger.info(
                "[%s] Fetched %d RSS entries", self.name, len(entries),
            )
            return entries

        except Exception as exc:
            logger.error("[%s] Failed to fetch RSS: %s", self.name, exc)
            return []

    async def try_wp_api(self, search_term: str) -> list[dict[str, Any]]:
        """Attempt to use WordPress REST API for targeted search.

        WordPress sites often expose /wp-json/wp/v2/posts endpoint
        which can be searched directly with query parameters.

        Args:
            search_term: Keyword to search for in post content.

        Returns:
            List of post dicts from WP API, or empty list if
            API is not available.
        """
        api_url = "https://arynews.tv/wp-json/wp/v2/posts"
        params = {
            "search": search_term,
            "per_page": 20,
            "orderby": "date",
            "order": "desc",
            "_fields": "id,date,title,link,excerpt,author",
        }

        try:
            response = await self.fetch(api_url, params=params)
            posts = response.json()

            if not isinstance(posts, list):
                logger.warning(
                    "[%s] WP API returned unexpected format for '%s'",
                    self.name, search_term,
                )
                return []

            entries: list[dict[str, Any]] = []
            for post in posts:
                # WP API returns rendered HTML in title and excerpt
                title_html = post.get("title", {})
                title = ""
                if isinstance(title_html, dict):
                    title = title_html.get("rendered", "")
                elif isinstance(title_html, str):
                    title = title_html

                # Strip HTML from title
                if "<" in title:
                    title = BeautifulSoup(title, "html.parser").get_text(strip=True)

                link = post.get("link", "")
                if not link:
                    continue

                excerpt_html = post.get("excerpt", {})
                summary = ""
                if isinstance(excerpt_html, dict):
                    summary = excerpt_html.get("rendered", "")
                elif isinstance(excerpt_html, str):
                    summary = excerpt_html
                if "<" in summary:
                    summary = BeautifulSoup(summary, "html.parser").get_text(strip=True)

                entries.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "published_date": post.get("date", ""),
                    "summary": summary.strip(),
                    "wp_api_source": True,
                })

            logger.info(
                "[%s] WP API returned %d posts for '%s'",
                self.name, len(entries), search_term,
            )
            return entries

        except Exception as exc:
            # WP API may be disabled (404/403) — this is expected
            logger.info(
                "[%s] WP API unavailable for '%s': %s",
                self.name, search_term, exc,
            )
            return []

    async def fetch_article(self, url: str) -> dict[str, Any]:
        """Fetch full article content from an ARY News URL.

        Args:
            url: Full URL to the ARY News article page.

        Returns:
            Dictionary with url, title, author, published_date,
            full_text, category, tags.
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

            # Extract article body from WordPress entry-content div
            full_text = ""
            content_selectors = [
                ("div", {"class": "entry-content"}),
                ("div", {"class": "single-post-content"}),
                ("div", {"class": "entry-content-wrap"}),
                ("div", {"class": "post-content"}),
                ("div", {"class": "article-content"}),
                ("div", {"class": "td-post-content"}),
            ]
            for tag_name, attrs in content_selectors:
                content_div = soup.find(tag_name, attrs)
                if content_div:
                    # Skip video-only articles: if no paragraph text, skip
                    paragraphs = content_div.find_all("p")
                    full_text = "\n\n".join(
                        p.get_text(strip=True)
                        for p in paragraphs
                        if p.get_text(strip=True)
                    )
                    if full_text:
                        break

            # Handle video-only articles: extract description from meta
            if not full_text:
                og_desc = soup.find("meta", property="og:description")
                if og_desc:
                    desc = og_desc.get("content", "")
                    if desc:
                        full_text = desc.strip()

            # Extract author
            author = ""
            author_selectors = [
                ("span", {"class": "author-name"}),
                ("a", {"class": "author-name"}),
                ("span", {"class": "td-post-author-name"}),
                ("a", {"rel": "author"}),
            ]
            for tag_name, attrs in author_selectors:
                author_tag = soup.find(tag_name, attrs)
                if author_tag:
                    author = author_tag.get_text(strip=True)
                    break
            if not author:
                author_meta = soup.find("meta", attrs={"name": "author"})
                if author_meta:
                    author = author_meta.get("content", "")

            # Extract published date
            published_date = ""
            time_tag = soup.find("time", class_="entry-date") or soup.find("time")
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
            cat_tag = soup.find("span", class_="td-post-category") or soup.find(
                "a", {"rel": "category tag"}
            )
            if cat_tag:
                category = cat_tag.get_text(strip=True)

            # Extract tags
            tags: list[str] = []
            tag_container = soup.find("div", class_="td-post-source-tags") or soup.find(
                "div", class_="post-tags"
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
        """Execute the ARY News scraping pipeline.

        Combines RSS feed monitoring with optional WP API search
        for higher coverage of trafficking-related content.

        Returns:
            List of article records matching trafficking keywords.
        """
        # 1. Fetch RSS feed entries
        rss_entries = await self.fetch_rss()

        # 2. Try WP API for targeted searches (run concurrently)
        wp_tasks = [self.try_wp_api(term) for term in WP_API_SEARCH_TERMS]
        wp_results = await asyncio.gather(*wp_tasks, return_exceptions=True)

        wp_entries: list[dict[str, Any]] = []
        for result in wp_results:
            if isinstance(result, list):
                wp_entries.extend(result)
            elif isinstance(result, Exception):
                logger.error("[%s] WP API error: %s", self.name, result)

        # 3. Merge and deduplicate by URL
        all_stubs = [*rss_entries, *wp_entries]
        seen_urls: set[str] = set()
        unique_stubs: list[dict[str, Any]] = []
        for stub in all_stubs:
            url = stub.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_stubs.append(stub)

        # Google News RSS fallback if no stubs from RSS or WP API
        if not unique_stubs:
            logger.info("[%s] No direct stubs, trying Google News fallback", self.name)
            try:
                response = await self.fetch(_GOOGLE_NEWS_ARY_FALLBACK)
                gn_parsed = await asyncio.to_thread(feedparser.parse, response.text)
                for entry in gn_parsed.entries:
                    link = entry.get("link", "")
                    if link and "arynews.tv" in link:
                        stub = {
                            "title": entry.get("title", "").strip(),
                            "url": link.strip(),
                            "published_date": entry.get("published", ""),
                        }
                        url = stub["url"]
                        if url not in seen_urls:
                            seen_urls.add(url)
                            unique_stubs.append(stub)
                logger.info(
                    "[%s] Google News fallback yielded %d stubs",
                    self.name, len(unique_stubs),
                )
            except Exception as exc:
                logger.error("[%s] Google News fallback failed: %s", self.name, exc)

        # Google News fallback if no stubs from direct sources
        if not unique_stubs:
            logger.info("[%s] No direct stubs, trying Google News fallback", self.name)
            try:
                response = await self.fetch(self.GOOGLE_NEWS_FALLBACK)
                gn_parsed = await asyncio.to_thread(feedparser.parse, response.text)
                for entry in gn_parsed.entries:
                    link = entry.get("link", "")
                    if link and "arynews.tv" in link and link not in seen_urls:
                        seen_urls.add(link)
                        unique_stubs.append({
                            "title": entry.get("title", "").strip(),
                            "url": link.strip(),
                            "published_date": entry.get("published", ""),
                        })
                logger.info(
                    "[%s] Google News fallback yielded %d ARY stubs",
                    self.name, len(unique_stubs),
                )
            except Exception as exc:
                logger.error("[%s] Google News fallback failed: %s", self.name, exc)

        if not unique_stubs:
            logger.warning("[%s] No article stubs found", self.name)
            return []

        logger.info(
            "[%s] %d unique articles (RSS: %d, WP API: %d)",
            self.name, len(unique_stubs), len(rss_entries), len(wp_entries),
        )

        # 4. Fetch full articles with concurrency limit
        semaphore = asyncio.Semaphore(5)

        async def _fetch_with_limit(stub: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                article = await self.fetch_article(stub["url"])
                if article:
                    # Merge stub metadata as fallback
                    if not article.get("title") and stub.get("title"):
                        article["title"] = stub["title"]
                    if not article.get("published_date") and stub.get("published_date"):
                        article["published_date"] = stub["published_date"]
                    if not article.get("author") and stub.get("author"):
                        article["author"] = stub["author"]
                return article

        tasks = [_fetch_with_limit(stub) for stub in unique_stubs]
        articles = await asyncio.gather(*tasks, return_exceptions=True)

        # 5. Filter by keywords
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
        """Validate a scraped ARY News article record.

        Args:
            record: A scraped article dictionary.

        Returns:
            True if required fields are present and valid.
        """
        required_fields = ["url", "title", "published_date", "full_text"]
        return all(record.get(f) for f in required_fields)
