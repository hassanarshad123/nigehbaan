"""Firecrawl integration for WAF-blocked and JS-rendered sites.

Provides async wrappers around the Firecrawl API (self-hosted or cloud).
Scrapers opt-in via ``use_firecrawl = True`` on their class.

Configuration via environment variables:
    FIRECRAWL_API_URL  — Base URL of self-hosted instance (e.g. http://72.61.124.88:3002)
    FIRECRAWL_API_KEY  — API key (required for cloud, optional for self-hosted)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)

def _get_firecrawl_url() -> str:
    return os.environ.get("FIRECRAWL_API_URL", "").rstrip("/")


def _get_firecrawl_key() -> str:
    return os.environ.get("FIRECRAWL_API_KEY", "")


@dataclass
class FirecrawlResponse:
    """Parsed response from a Firecrawl scrape/crawl request."""

    success: bool
    html: str = ""
    markdown: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def is_firecrawl_configured() -> bool:
    """Check if Firecrawl is configured and available."""
    return bool(_get_firecrawl_url())


async def firecrawl_scrape(
    url: str,
    formats: list[str] | None = None,
    timeout: float = 60.0,
    wait_for: int = 0,
    actions: list[dict[str, Any]] | None = None,
) -> FirecrawlResponse:
    """Scrape a single URL via Firecrawl API.

    Args:
        url: The URL to scrape.
        formats: Output formats — ["html", "markdown"]. Defaults to both.
        timeout: Request timeout in seconds.
        wait_for: Milliseconds to wait after page load (for JS rendering).
        actions: Browser actions to perform (click, type, etc.).

    Returns:
        FirecrawlResponse with HTML, markdown, and metadata.
    """
    fc_url = _get_firecrawl_url()
    if not fc_url:
        return FirecrawlResponse(
            success=False,
            error="Firecrawl not configured. Set FIRECRAWL_API_URL.",
        )

    payload: dict[str, Any] = {
        "url": url,
        "formats": formats or ["html", "markdown"],
    }
    if wait_for:
        payload["waitFor"] = wait_for
    if actions:
        payload["actions"] = actions

    headers: dict[str, str] = {"Content-Type": "application/json"}
    fc_key = _get_firecrawl_key()
    if fc_key:
        headers["Authorization"] = f"Bearer {fc_key}"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.post(
                f"{fc_url}/v1/scrape",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                result_data = data.get("data", {})
                return FirecrawlResponse(
                    success=True,
                    html=result_data.get("html", ""),
                    markdown=result_data.get("markdown", ""),
                    metadata=result_data.get("metadata", {}),
                    raw=data,
                )
            return FirecrawlResponse(
                success=False,
                error=data.get("error", "Unknown Firecrawl error"),
                raw=data,
            )

    except Exception as exc:
        logger.error("Firecrawl scrape failed for %s: %s", url, exc)
        return FirecrawlResponse(success=False, error=str(exc))


async def firecrawl_crawl(
    url: str,
    include_patterns: list[str] | None = None,
    max_pages: int = 50,
    timeout: float = 120.0,
) -> list[FirecrawlResponse]:
    """Crawl a site via Firecrawl API (follows links).

    Args:
        url: Starting URL.
        include_patterns: URL patterns to follow (glob-style).
        max_pages: Maximum pages to crawl.
        timeout: Request timeout in seconds.

    Returns:
        List of FirecrawlResponse for each crawled page.
    """
    fc_url = _get_firecrawl_url()
    if not fc_url:
        return [FirecrawlResponse(
            success=False,
            error="Firecrawl not configured. Set FIRECRAWL_API_URL.",
        )]

    payload: dict[str, Any] = {
        "url": url,
        "limit": max_pages,
    }
    if include_patterns:
        payload["includePaths"] = include_patterns

    headers: dict[str, str] = {"Content-Type": "application/json"}
    fc_key = _get_firecrawl_key()
    if fc_key:
        headers["Authorization"] = f"Bearer {fc_key}"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.post(
                f"{fc_url}/v1/crawl",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            results: list[FirecrawlResponse] = []
            for page in data.get("data", []):
                results.append(FirecrawlResponse(
                    success=True,
                    html=page.get("html", ""),
                    markdown=page.get("markdown", ""),
                    metadata=page.get("metadata", {}),
                    raw=page,
                ))
            return results

    except Exception as exc:
        logger.error("Firecrawl crawl failed for %s: %s", url, exc)
        return [FirecrawlResponse(success=False, error=str(exc))]
