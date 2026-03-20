"""Base scraper module for Nigehbaan data pipeline.

All scrapers inherit from BaseScraper, which provides common infrastructure
for HTTP requests, rate limiting, raw data storage, and run tracking.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import asyncio
import json
import logging

import httpx

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")

# Common child protection keywords shared across all scrapers
TRAFFICKING_KEYWORDS: list[str] = [
    # Trafficking & exploitation
    "child trafficking", "human trafficking", "traffick", "smuggling",
    "forced labor", "forced labour", "bonded lab", "bonded labour",
    "modern slavery", "debt bondage", "slavery",
    # Sexual abuse
    "sexual abuse", "rape", "molestation", "sodomy", "incest",
    "child sexual", "CSA",
    # Kidnapping & missing
    "kidnap", "abduct", "missing child", "missing girl", "missing boy",
    "disappeared",
    # Online exploitation
    "child pornograph", "CSAM", "grooming", "sextortion", "PECA",
    "online exploit",
    # Child labor
    "child lab", "child work", "brick kiln", "bhatta", "minor employ",
    # Child marriage
    "child marriage", "early marriage", "underage marriage",
    # Physical abuse & murder
    "physical abuse", "torture", "violence against child",
    "child murder", "infanticide", "honor killing", "honour killing",
    # Begging & organ
    "begging ring", "organ trafficking", "camel jockey",
    # Legal codes
    "366-A", "366-B", "370", "371", "377", "292-A", "292-B", "zina",
    # Institutional
    "FIA", "child protection", "Zainab Alert",
    # General
    "child abuse", "child exploit",
    "minor girl", "minor boy", "minor victim", "minor age",
    "abandonment", "abandoned child", "medical negligence",
]


class BaseScraper(ABC):
    """Abstract base class for all Nigehbaan scrapers.

    Provides common infrastructure: async HTTP client, rate limiting,
    raw data storage, and run tracking.

    Subclasses must implement:
        - scrape(): Execute the scraping logic
        - validate(): Validate a single scraped record

    Attributes:
        name: Identifier for this scraper (used in logging and file keys).
        source_url: The primary URL this scraper targets.
        schedule: Cron expression defining how often this scraper runs.
        priority: Priority tier (P0, P1, P2, P3) from sources.yaml.
    """

    name: str = "base"
    source_url: str = ""
    schedule: str = ""
    priority: str = "P2"

    # Rate limiting defaults (seconds between requests)
    rate_limit_delay: float = 1.0  # 1s for news, 2s for gov sites
    request_timeout: float = 30.0
    max_retries: int = 3

    def __init__(self) -> None:
        self.run_id: str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the shared httpx async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.request_timeout),
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Nigehbaan-DataPipeline/1.0 "
                        "(Anti-Trafficking Research; +https://nigehbaan.pk)"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Fetch a URL with retry logic and rate limiting.

        Args:
            url: URL to fetch.
            method: HTTP method (GET or POST).
            headers: Additional headers to merge.
            data: Form data for POST requests.
            params: Query parameters.

        Returns:
            httpx.Response object.

        Raises:
            httpx.HTTPStatusError: If response status >= 400 after retries.
        """
        client = await self.get_client()

        for attempt in range(1, self.max_retries + 1):
            try:
                if method.upper() == "POST":
                    response = await client.post(
                        url, data=data, params=params, headers=headers
                    )
                else:
                    response = await client.get(
                        url, params=params, headers=headers
                    )
                response.raise_for_status()
                await asyncio.sleep(self.rate_limit_delay)
                return response
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                if attempt == self.max_retries:
                    logger.error(
                        "[%s] Failed after %d attempts: %s — %s",
                        self.name, self.max_retries, url, exc,
                    )
                    raise
                backoff = 2 ** attempt
                logger.warning(
                    "[%s] Attempt %d/%d failed for %s, retrying in %ds",
                    self.name, attempt, self.max_retries, url, backoff,
                )
                await asyncio.sleep(backoff)

        raise RuntimeError("Unreachable")  # pragma: no cover

    async def fetch_bytes(self, url: str) -> bytes:
        """Fetch raw bytes (for PDF/binary downloads).

        Args:
            url: URL to download.

        Returns:
            Raw response bytes.
        """
        response = await self.fetch(url)
        return response.content

    def matches_keywords(
        self, text: str, keywords: list[str] | None = None
    ) -> bool:
        """Check if text contains any trafficking-related keywords.

        Args:
            text: Combined title + body text.
            keywords: Optional custom keyword list.

        Returns:
            True if any keyword is found (case-insensitive).
        """
        search_keywords = keywords or TRAFFICKING_KEYWORDS
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in search_keywords)

    @abstractmethod
    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the scraping logic.

        Returns:
            List of raw records as dictionaries.
        """
        ...

    @abstractmethod
    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a single scraped record.

        Args:
            record: A dictionary representing one scraped item.

        Returns:
            True if the record passes validation.
        """
        ...

    def get_raw_dir(self) -> Path:
        """Get the raw data directory for this scraper."""
        raw_dir = RAW_DATA_DIR / self.name
        raw_dir.mkdir(parents=True, exist_ok=True)
        return raw_dir

    async def save_raw(
        self, data: list[dict[str, Any]], format: str = "json"
    ) -> Path:
        """Save raw scraped data to local files.

        Args:
            data: List of validated records to persist.
            format: Storage format — 'json' or 'csv'.

        Returns:
            Path where the data was stored.
        """
        raw_dir = self.get_raw_dir()
        file_path = raw_dir / f"{self.run_id}.{format}"

        if format == "json":
            file_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        elif format == "csv":
            import csv
            import io

            if not data:
                file_path.write_text("", encoding="utf-8")
            else:
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                file_path.write_text(output.getvalue(), encoding="utf-8")

        logger.info("[%s] Saved %d records to %s", self.name, len(data), file_path)
        return file_path

    async def log_run(
        self,
        records_count: int,
        status: str = "success",
        error: str | None = None,
    ) -> None:
        """Log scraper run metadata.

        Args:
            records_count: Number of valid records produced.
            status: One of 'success', 'error', 'partial'.
            error: Error message if status is 'error'.
        """
        log_msg = f"[{self.name}] {status}: {records_count} records"
        if error:
            log_msg += f" — {error}"
        logger.info(log_msg)

    async def run(self) -> list[dict[str, Any]]:
        """Full scraper execution pipeline: scrape -> validate -> save -> log.

        Returns:
            List of validated records.
        """
        try:
            raw_data = await self.scrape()
            valid_data = [r for r in raw_data if self.validate(r)]
            if valid_data:
                await self.save_raw(valid_data)
            await self.log_run(len(valid_data))
            return valid_data
        except Exception as e:
            await self.log_run(0, status="error", error=str(e))
            raise
        finally:
            await self.close()
