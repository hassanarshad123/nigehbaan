"""Geo News scraper for child trafficking and abuse articles.

Scrapes Geo News (geo.tv) which relies heavily on JavaScript
rendering. No RSS feed is available, requiring a headless browser
approach via Playwright for reliable content extraction.

Strategy:
    1. Use Playwright to render geo.tv search/listing pages
    2. Execute search queries for trafficking-related terms
    3. Navigate paginated results
    4. Extract full article text from rendered DOM
    5. Handle dynamic content loading (infinite scroll, AJAX)

Schedule: Daily (0 2 * * *) — less frequent due to browser overhead
Priority: P1 — Major Urdu/English news network, but harder to scrape
"""

from datetime import datetime, timezone
from typing import Any

import asyncio
import logging

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Playwright import with graceful degradation
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning(
        "Playwright is not installed. GeoScraper will not be able to "
        "scrape JavaScript-rendered pages. Install with: pip install playwright "
        "&& python -m playwright install chromium"
    )


class GeoScraper(BaseScraper):
    """Scraper for Geo News articles on child trafficking.

    Geo News relies heavily on client-side JavaScript rendering,
    making traditional HTTP+BS4 scraping unreliable. This scraper
    uses Playwright for headless browser automation.

    Note: Playwright adds significant overhead per page load (~2-5s).
    Schedule is set to daily to balance coverage with resource usage.

    Attributes:
        name: Scraper identifier.
        source_url: Geo News search URL template.
        schedule: Daily cron expression.
        priority: P1 but with daily schedule due to JS rendering cost.
    """

    name: str = "geo_news"
    source_url: str = "https://www.geo.tv"
    search_url: str = "https://www.geo.tv/search/{query}"
    schedule: str = "0 2 * * *"
    priority: str = "P1"

    SEARCH_QUERIES: list[str] = [
        "child trafficking",
        "child abuse",
        "missing children",
        "kidnapping",
        "bonded labour",
        "human trafficking",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None

    async def init_browser(self) -> None:
        """Initialize Playwright browser instance.

        Creates a headless Chromium browser with appropriate
        viewport and user-agent settings to avoid detection.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error(
                "[%s] Cannot initialize browser: Playwright not installed",
                self.name,
            )
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-PK",
        )
        # Block unnecessary resources to speed up loading
        await self._context.route(
            "**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,eot}",
            lambda route: route.abort(),
        )
        await self._context.route(
            "**/*{analytics,tracking,ads,doubleclick,googlesyndication}*",
            lambda route: route.abort(),
        )

        logger.info("[%s] Browser initialized", self.name)

    async def close_browser(self) -> None:
        """Close the Playwright browser and cleanup resources."""
        if self._context:
            try:
                await self._context.close()
            except Exception as exc:
                logger.warning("[%s] Error closing context: %s", self.name, exc)
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception as exc:
                logger.warning("[%s] Error closing browser: %s", self.name, exc)
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as exc:
                logger.warning("[%s] Error stopping playwright: %s", self.name, exc)
            self._playwright = None

        logger.info("[%s] Browser closed", self.name)

    async def search_articles(self, query: str) -> list[str]:
        """Search Geo News for articles matching a query.

        Uses Playwright to render the search page, wait for
        results to load, and extract article URLs.

        Args:
            query: Search term to look for.

        Returns:
            List of article URLs from search results.
        """
        if not self._context:
            logger.error("[%s] Browser not initialized", self.name)
            return []

        search_url = self.search_url.format(query=query.replace(" ", "%20"))
        page: Any = None

        try:
            page = await self._context.new_page()
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

            # Wait for search results to render
            try:
                await page.wait_for_selector(
                    "a[href*='/latest/'],"
                    "a[href*='/article/'],"
                    ".search-result a,"
                    ".listing a,"
                    "h2 a",
                    timeout=15000,
                )
            except Exception:
                logger.warning(
                    "[%s] Search results selector timeout for '%s'",
                    self.name, query,
                )

            # Extract all article links from the page
            links = await page.evaluate("""
                () => {
                    const urls = new Set();
                    const anchors = document.querySelectorAll('a[href]');
                    for (const a of anchors) {
                        const href = a.href;
                        // Geo.tv article URLs typically contain /latest/ or numeric ID patterns
                        if (href && href.includes('geo.tv') &&
                            (href.match(/\\/\\d{6}/) || href.includes('/latest/') ||
                             href.includes('/article/'))) {
                            // Exclude non-article pages
                            if (!href.includes('/category/') &&
                                !href.includes('/author/') &&
                                !href.includes('/tag/') &&
                                !href.includes('/page/')) {
                                urls.add(href);
                            }
                        }
                    }
                    return Array.from(urls);
                }
            """)

            logger.info(
                "[%s] Found %d article URLs for query '%s'",
                self.name, len(links), query,
            )
            return links

        except Exception as exc:
            logger.error(
                "[%s] Search failed for '%s': %s", self.name, query, exc,
            )
            return []

        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass

    async def fetch_article(self, url: str) -> dict[str, Any]:
        """Fetch full article content using Playwright.

        Navigates to the article page, waits for content to
        render, and extracts text from the DOM.

        Args:
            url: Full URL to the Geo News article.

        Returns:
            Dictionary with url, title, author, published_date,
            full_text, category.
        """
        if not self._context:
            logger.error("[%s] Browser not initialized", self.name)
            return {}

        page: Any = None

        try:
            page = await self._context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for article content to render
            try:
                await page.wait_for_selector(
                    "article, .article-content, .story-detail, h1",
                    timeout=10000,
                )
            except Exception:
                logger.warning(
                    "[%s] Article content selector timeout for %s",
                    self.name, url,
                )

            # Extract article data from the rendered DOM
            article_data = await page.evaluate("""
                () => {
                    // Extract title
                    let title = '';
                    const h1 = document.querySelector('h1');
                    if (h1) title = h1.innerText.trim();
                    if (!title) {
                        const ogTitle = document.querySelector('meta[property="og:title"]');
                        if (ogTitle) title = ogTitle.getAttribute('content') || '';
                    }

                    // Extract article body text
                    let fullText = '';
                    const contentSelectors = [
                        '.content-area p',
                        '.article-content p',
                        '.story-detail p',
                        'article p',
                        '.single-article-content p',
                    ];
                    for (const selector of contentSelectors) {
                        const paragraphs = document.querySelectorAll(selector);
                        if (paragraphs.length > 0) {
                            fullText = Array.from(paragraphs)
                                .map(p => p.innerText.trim())
                                .filter(t => t.length > 0)
                                .join('\\n\\n');
                            if (fullText) break;
                        }
                    }
                    // Fallback: get text from any visible article-like container
                    if (!fullText) {
                        const article = document.querySelector('article') ||
                                       document.querySelector('.post-content');
                        if (article) {
                            fullText = article.innerText.trim();
                        }
                    }

                    // Extract author
                    let author = '';
                    const authorSelectors = [
                        '.author-name', '.story-author', 'a[rel="author"]',
                        '.post-author', 'span.author',
                    ];
                    for (const sel of authorSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.innerText.trim()) {
                            author = el.innerText.trim();
                            break;
                        }
                    }
                    if (!author) {
                        const metaAuthor = document.querySelector('meta[name="author"]');
                        if (metaAuthor) author = metaAuthor.getAttribute('content') || '';
                    }

                    // Extract published date
                    let publishedDate = '';
                    const timeEl = document.querySelector('time');
                    if (timeEl) {
                        publishedDate = timeEl.getAttribute('datetime') ||
                                       timeEl.innerText.trim();
                    }
                    if (!publishedDate) {
                        const dateMeta = document.querySelector(
                            'meta[property="article:published_time"]'
                        );
                        if (dateMeta) {
                            publishedDate = dateMeta.getAttribute('content') || '';
                        }
                    }
                    // Fallback: look for date-like spans
                    if (!publishedDate) {
                        const dateSelectors = ['.date', '.post-date', '.story-date'];
                        for (const sel of dateSelectors) {
                            const el = document.querySelector(sel);
                            if (el && el.innerText.trim()) {
                                publishedDate = el.innerText.trim();
                                break;
                            }
                        }
                    }

                    // Extract category
                    let category = '';
                    const catSelectors = [
                        '.category-name', '.post-category',
                        'a[rel="category tag"]', '.breadcrumb a',
                    ];
                    for (const sel of catSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.innerText.trim()) {
                            category = el.innerText.trim();
                            break;
                        }
                    }

                    return { title, fullText, author, publishedDate, category };
                }
            """)

            return {
                "url": url,
                "title": article_data.get("title", ""),
                "author": article_data.get("author", ""),
                "published_date": article_data.get("publishedDate", ""),
                "full_text": article_data.get("fullText", ""),
                "source": "geo_news",
                "category": article_data.get("category", ""),
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            logger.error(
                "[%s] Failed to fetch article %s: %s", self.name, url, exc,
            )
            return {}

        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the Geo News scraping pipeline.

        Initializes browser, runs all search queries, collects
        and deduplicates article URLs, fetches full content,
        and cleans up browser resources.

        Returns:
            List of article records matching trafficking keywords.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error(
                "[%s] Playwright not installed — cannot scrape Geo News. "
                "Install with: pip install playwright && python -m playwright install chromium",
                self.name,
            )
            return []

        try:
            # 1. Initialize Playwright browser
            await self.init_browser()
            if not self._context:
                logger.error("[%s] Failed to initialize browser", self.name)
                return []

            # 2. Search for articles across all queries
            all_urls: list[str] = []
            for query in self.SEARCH_QUERIES:
                urls = await self.search_articles(query)
                all_urls.extend(urls)
                # Small delay between searches to avoid rate limiting
                await asyncio.sleep(2)

            # 3. Deduplicate URLs
            unique_urls = list(dict.fromkeys(all_urls))  # preserves order
            logger.info(
                "[%s] %d unique article URLs from %d total across %d queries",
                self.name, len(unique_urls), len(all_urls), len(self.SEARCH_QUERIES),
            )

            if not unique_urls:
                logger.warning("[%s] No article URLs found", self.name)
                return []

            # 4. Fetch full articles (sequentially to avoid overwhelming the browser)
            articles: list[dict[str, Any]] = []
            for url in unique_urls:
                try:
                    article = await self.fetch_article(url)
                    if article and article.get("url"):
                        # Filter by keywords
                        combined_text = (
                            f"{article.get('title', '')} "
                            f"{article.get('full_text', '')}"
                        )
                        if self.matches_keywords(combined_text):
                            articles.append(article)
                except Exception as exc:
                    logger.error(
                        "[%s] Error fetching %s: %s", self.name, url, exc,
                    )
                # Brief pause between article fetches
                await asyncio.sleep(1)

            logger.info(
                "[%s] Found %d matching articles out of %d unique URLs",
                self.name, len(articles), len(unique_urls),
            )
            return articles

        except Exception as exc:
            logger.error("[%s] Scrape pipeline error: %s", self.name, exc)
            return []

        finally:
            # 5. Always close browser
            await self.close_browser()

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a scraped Geo News article record.

        Args:
            record: A scraped article dictionary.

        Returns:
            True if required fields are present and valid.
        """
        required_fields = ["url", "title", "published_date", "full_text"]
        return all(record.get(f) for f in required_fields)
