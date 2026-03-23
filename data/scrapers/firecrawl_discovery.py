"""Firecrawl Agent-powered autonomous discovery of child trafficking data.

Uses Firecrawl's extract + search capabilities to autonomously discover
new articles, reports, and data about child trafficking in Pakistan
without requiring pre-configured URLs.

Schedule: Weekly via Celery Beat
Priority: P1 — discovers new sources we don't know about
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from data.scrapers.firecrawl_client import (
    firecrawl_extract,
    firecrawl_map,
    is_firecrawl_configured,
)

logger = logging.getLogger(__name__)

# Search queries covering all aspects of child protection in Pakistan
DISCOVERY_QUERIES = [
    "child trafficking Pakistan 2024 2025 2026",
    "bonded labor brick kiln Pakistan children",
    "missing children Pakistan kidnapping",
    "child marriage Pakistan latest",
    "child abuse Pakistan court judgment",
    "child labor exploitation Pakistan news",
    "begging mafia children Pakistan",
    "ZARRA missing children Pakistan",
    "Sahil cruel numbers child abuse",
    "FIA anti human trafficking Pakistan",
]

# JSON schema for structured extraction from discovered pages
ARTICLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Article headline or report title"},
        "url": {"type": "string", "description": "Source URL"},
        "published_date": {"type": "string", "description": "Publication date (ISO format if possible)"},
        "summary": {"type": "string", "description": "2-3 sentence summary of the content"},
        "location": {"type": "string", "description": "Location mentioned (city, district, province)"},
        "incident_type": {
            "type": "string",
            "description": "Type of incident",
            "enum": [
                "kidnapping", "child_trafficking", "sexual_abuse", "child_labor",
                "bonded_labor", "child_marriage", "missing", "begging_ring",
                "organ_trafficking", "child_murder", "other",
            ],
        },
        "victim_count": {"type": "integer", "description": "Number of victims mentioned"},
        "source_type": {
            "type": "string",
            "description": "Type of source",
            "enum": ["news", "government", "ngo", "court", "research"],
        },
    },
    "required": ["title", "url"],
}

# Known Pakistan news and government domains to search for URLs
DISCOVERY_DOMAINS = [
    "https://www.dawn.com",
    "https://tribune.com.pk",
    "https://www.thenews.com.pk",
    "https://www.geo.tv",
    "https://www.samaa.tv",
    "https://sahil.org",
    "https://www.mohr.gov.pk",
    "https://ncrc.gov.pk",
]


class FirecrawlDiscoveryScraper:
    """Autonomous data discovery scraper using Firecrawl.

    Two modes of operation:
    1. Domain mapping — discover URLs on known sites we haven't scraped
    2. Schema extraction — extract structured data from discovered pages
    """

    name: str = "firecrawl_discovery"

    async def run(self) -> list[dict[str, Any]]:
        """Run the discovery pipeline and return discovered articles."""
        if not is_firecrawl_configured():
            logger.warning("[%s] Firecrawl not configured — skipping discovery", self.name)
            return []

        all_records: list[dict[str, Any]] = []

        # Phase 1: Map known domains for new URLs
        for domain in DISCOVERY_DOMAINS:
            try:
                urls = await firecrawl_map(
                    url=domain,
                    search="child trafficking abuse missing kidnapping labor",
                    limit=50,
                )
                if urls:
                    logger.info(
                        "[%s] Discovered %d URLs on %s",
                        self.name, len(urls), domain,
                    )
                    # Extract structured data from discovered URLs
                    result = await firecrawl_extract(
                        urls=urls[:20],  # limit to top 20 per domain
                        schema=ARTICLE_SCHEMA,
                        prompt="Extract article information about child trafficking, abuse, kidnapping, bonded labor, or child marriage in Pakistan.",
                    )
                    if result.success and result.data:
                        records = result.data if isinstance(result.data, list) else [result.data]
                        for record in records:
                            record["discovery_source"] = domain
                            record["discovered_at"] = datetime.now(timezone.utc).isoformat()
                        all_records.extend(records)
            except Exception as exc:
                logger.warning("[%s] Discovery failed for %s: %s", self.name, domain, exc)

        logger.info("[%s] Total discovered: %d records", self.name, len(all_records))
        return all_records
