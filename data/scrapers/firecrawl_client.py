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


# ---------------------------------------------------------------------------
# Advanced features — structured extraction, URL discovery, PDF parsing
# ---------------------------------------------------------------------------


@dataclass
class FirecrawlExtractResponse:
    """Parsed response from a Firecrawl extract request."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


async def firecrawl_extract(
    urls: list[str],
    schema: dict[str, Any] | None = None,
    prompt: str | None = None,
    timeout: float = 120.0,
) -> FirecrawlExtractResponse:
    """Extract structured data from URLs using Firecrawl's LLM-powered extraction.

    Args:
        urls: URLs to extract from (supports wildcards like "example.com/*").
        schema: JSON Schema defining the output structure.
        prompt: Natural language description of what to extract.
        timeout: Request timeout in seconds.

    Returns:
        FirecrawlExtractResponse with structured data matching the schema.
    """
    fc_url = _get_firecrawl_url()
    if not fc_url:
        return FirecrawlExtractResponse(
            success=False,
            error="Firecrawl not configured. Set FIRECRAWL_API_URL.",
        )

    payload: dict[str, Any] = {"urls": urls}
    if schema:
        payload["schema"] = schema
    if prompt:
        payload["prompt"] = prompt

    headers = _build_headers()

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.post(
                f"{fc_url}/v1/extract",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                return FirecrawlExtractResponse(
                    success=True,
                    data=data.get("data", {}),
                    raw=data,
                )
            return FirecrawlExtractResponse(
                success=False,
                error=data.get("error", "Unknown Firecrawl extract error"),
                raw=data,
            )

    except Exception as exc:
        logger.error("Firecrawl extract failed for %s: %s", urls, exc)
        return FirecrawlExtractResponse(success=False, error=str(exc))


async def firecrawl_map(
    url: str,
    search: str | None = None,
    limit: int = 5000,
    timeout: float = 30.0,
) -> list[str]:
    """Discover all URLs on a website using Firecrawl's map endpoint.

    Args:
        url: The base URL to map (e.g. "https://data.lhc.gov.pk").
        search: Optional search query to filter URLs.
        limit: Maximum number of URLs to return.
        timeout: Request timeout in seconds.

    Returns:
        List of discovered URLs, or empty list on error.
    """
    fc_url = _get_firecrawl_url()
    if not fc_url:
        logger.warning("Firecrawl not configured — cannot map %s", url)
        return []

    payload: dict[str, Any] = {"url": url, "limit": limit}
    if search:
        payload["search"] = search

    headers = _build_headers()

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.post(
                f"{fc_url}/v1/map",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                return data.get("links", [])
            logger.warning("Firecrawl map failed for %s: %s", url, data.get("error"))
            return []

    except Exception as exc:
        logger.error("Firecrawl map failed for %s: %s", url, exc)
        return []


async def firecrawl_scrape_with_actions(
    url: str,
    actions: list[dict[str, Any]],
    formats: list[str] | None = None,
    timeout: float = 90.0,
) -> FirecrawlResponse:
    """Scrape a URL after performing browser actions (click, type, scroll, wait).

    This enables automated form submission, pagination, and interaction
    with dynamic JS-rendered content before extraction.

    Actions format:
        [
            {"type": "wait", "milliseconds": 2000},
            {"type": "click", "selector": "#search-button"},
            {"type": "type", "selector": "#input-field", "text": "query"},
            {"type": "press", "key": "Enter"},
            {"type": "scroll", "direction": "down", "amount": 500},
        ]
    """
    return await firecrawl_scrape(
        url=url,
        formats=formats,
        timeout=timeout,
        actions=actions,
    )


async def firecrawl_parse_pdf(
    url: str,
    timeout: float = 90.0,
) -> FirecrawlResponse:
    """Extract text from a PDF document via Firecrawl.

    Firecrawl automatically detects PDFs and applies text extraction
    with OCR fallback for scanned documents.

    Args:
        url: Direct URL to the PDF file.
        timeout: Request timeout in seconds.

    Returns:
        FirecrawlResponse with markdown/text content of the PDF.
    """
    return await firecrawl_scrape(
        url=url,
        formats=["markdown"],
        timeout=timeout,
    )


def _build_headers() -> dict[str, str]:
    """Build common request headers with optional auth."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    fc_key = _get_firecrawl_key()
    if fc_key:
        headers["Authorization"] = f"Bearer {fc_key}"
    return headers
