"""Base API scraper for Nigehbaan data pipeline.

Extends BaseScraper with REST API / CSV download capabilities:
JSON fetching, auto-pagination, CSV download and parsing.
"""

from pathlib import Path
from typing import Any

import csv
import io
import logging

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BaseAPIScraper(BaseScraper):
    """Base class for scrapers that consume REST APIs or CSV downloads.

    Provides JSON fetching with error handling, auto-pagination,
    CSV download, and CSV parsing.
    """

    async def fetch_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict | list:
        """Fetch JSON from a URL with error handling.

        Args:
            url: API endpoint URL.
            params: Query parameters.
            headers: Additional headers.

        Returns:
            Parsed JSON response (dict or list).
        """
        response = await self.fetch(url, params=params, headers=headers)
        return response.json()

    async def fetch_paginated(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        page_key: str = "page",
        results_key: str = "results",
        max_pages: int = 100,
    ) -> list[dict]:
        """Auto-paginate through a REST API.

        Args:
            url: API endpoint URL.
            params: Base query parameters (page param added automatically).
            page_key: Query parameter name for page number.
            results_key: Key in response JSON containing the result list.
            max_pages: Safety limit on pages to fetch.

        Returns:
            Combined list of all result records across pages.
        """
        all_results: list[dict] = []
        params = dict(params or {})
        page = 1

        while page <= max_pages:
            params[page_key] = page
            response = await self.fetch(url, params=params)
            data = response.json()

            if isinstance(data, list):
                if not data:
                    break
                all_results.extend(data)
                if len(data) < params.get("per_page", params.get("pageSize", 50)):
                    break
            elif isinstance(data, dict):
                results = data.get(results_key, [])
                if not results:
                    break
                all_results.extend(results)

                # Check if more pages exist
                total = data.get("total", data.get("totalResults", 0))
                per_page = data.get("per_page", data.get("pageSize", len(results)))
                if page * per_page >= total:
                    break
            else:
                break

            page += 1

        logger.info(
            "[%s] Fetched %d records across %d pages from %s",
            self.name, len(all_results), page, url,
        )
        return all_results

    async def fetch_csv_download(self, url: str) -> Path:
        """Download a CSV file to local storage.

        Args:
            url: URL of the CSV file.

        Returns:
            Path to the downloaded CSV file.
        """
        raw_dir = self.get_raw_dir()
        filename = url.split("/")[-1].split("?")[0]
        if not filename.endswith(".csv"):
            filename = f"{self.name}_{self.run_id}.csv"
        file_path = raw_dir / filename

        response = await self.fetch(url)
        file_path.write_text(response.text, encoding="utf-8")
        logger.info("[%s] Downloaded CSV: %s", self.name, file_path)
        return file_path

    def parse_csv(
        self, path: Path, delimiter: str = ","
    ) -> list[dict[str, str]]:
        """Parse a CSV file into a list of record dicts.

        Args:
            path: Path to the CSV file.
            delimiter: Column delimiter character.

        Returns:
            List of dicts, one per row, keyed by header names.
        """
        records: list[dict[str, str]] = []
        try:
            text = path.read_text(encoding="utf-8")
            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            for row in reader:
                records.append(dict(row))
        except Exception as exc:
            logger.error("[%s] CSV parse error for %s: %s", self.name, path, exc)

        logger.info("[%s] Parsed %d rows from %s", self.name, len(records), path.name)
        return records
