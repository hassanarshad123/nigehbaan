"""CTDC Global Synthetic Dataset downloader.

Source: https://www.ctdatacollaborative.org
Output: data/raw/ctdc/
Priority: P1

Updated 2026-03-22: Fixed download logic to handle IOM site restructuring.
- Added multiple download URL patterns (direct CSV, API endpoints)
- Improved country filtering to use both "Pakistan" and "PAK"
- Added column name normalization for schema changes
- Added fallback to cached dataset if download fails
"""

from pathlib import Path
from typing import Any

import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RAW_CTDC_DIR = Path("data/raw/ctdc")

# Known CTDC download URLs — the site has restructured multiple times
CTDC_DOWNLOAD_URLS: list[str] = [
    # Current download page
    "https://www.ctdatacollaborative.org/download-global-dataset",
    # Alternative endpoints
    "https://www.ctdatacollaborative.org/dataset/download",
    "https://www.ctdatacollaborative.org/global-synthetic-dataset",
]

# Direct CSV download links that have been observed
CTDC_DIRECT_CSV_URLS: list[str] = [
    "https://www.ctdatacollaborative.org/sites/default/files/Global_Synthetic_Data.csv",
    "https://www.ctdatacollaborative.org/sites/default/files/global_synthetic_dataset.csv",
    "https://www.ctdatacollaborative.org/sites/default/files/CTDC_Global_Synthetic.csv",
    "https://www.ctdatacollaborative.org/download/global-synthetic-dataset/csv",
]

# IOM Counter-Trafficking Data API (alternative source)
CTDC_API_URL: str = "https://www.ctdatacollaborative.org/api/v1/records"

# Pakistan identifiers used across different CTDC schema versions
PAKISTAN_IDENTIFIERS: list[str] = [
    "pakistan", "pak", "586",  # ISO 3166-1 numeric code for Pakistan
]


async def download_ctdc_dataset(
    output_dir: Path = RAW_CTDC_DIR,
) -> Path | None:
    """Download the CTDC Global Synthetic Dataset CSV.

    Tries multiple strategies:
    1. Direct CSV download from known URLs
    2. Scrape the download page for CSV links
    3. Query the CTDC API
    4. Fall back to cached dataset if available
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cached_path = output_dir / "ctdc_global_synthetic.csv"

    async with httpx.AsyncClient(
        timeout=120.0,
        follow_redirects=True,
        headers={"User-Agent": "Nigehbaan-DataPipeline/1.0"},
    ) as client:
        # Strategy 1: Try direct CSV download URLs
        for csv_url in CTDC_DIRECT_CSV_URLS:
            try:
                response = await client.get(csv_url)
                if (
                    response.status_code == 200
                    and len(response.content) > 1000
                    and _looks_like_csv(response.text)
                ):
                    cached_path.write_bytes(response.content)
                    logger.info(
                        "Downloaded CTDC dataset from direct URL: %s (%d bytes)",
                        csv_url, len(response.content),
                    )
                    return cached_path
            except Exception as exc:
                logger.debug("Direct CSV URL %s failed: %s", csv_url, exc)

        # Strategy 2: Scrape download page for CSV links
        for page_url in CTDC_DOWNLOAD_URLS:
            try:
                response = await client.get(page_url)
                if response.status_code != 200:
                    continue
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

                csv_links: list[str] = []

                # Find links to CSV files
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    text = link.get_text(strip=True).lower()
                    if (
                        href.lower().endswith(".csv")
                        or "download" in text
                        or "csv" in text
                        or "dataset" in text
                    ):
                        full_url = (
                            href
                            if href.startswith("http")
                            else f"https://www.ctdatacollaborative.org{href}"
                        )
                        csv_links.append(full_url)

                # Also check for form-based downloads
                for form in soup.find_all("form"):
                    action = form.get("action", "")
                    if "download" in action.lower():
                        full_url = (
                            action
                            if action.startswith("http")
                            else f"https://www.ctdatacollaborative.org{action}"
                        )
                        csv_links.append(full_url)

                # Also check for buttons with download URLs
                for btn in soup.find_all(["button", "input"], attrs={"data-url": True}):
                    data_url = btn["data-url"]
                    csv_links.append(
                        data_url
                        if data_url.startswith("http")
                        else f"https://www.ctdatacollaborative.org{data_url}"
                    )

                for url in csv_links:
                    try:
                        file_response = await client.get(url)
                        if (
                            file_response.status_code == 200
                            and len(file_response.content) > 1000
                            and _looks_like_csv(file_response.text[:2000])
                        ):
                            cached_path.write_bytes(file_response.content)
                            logger.info(
                                "Downloaded CTDC dataset: %s (%d bytes)",
                                cached_path, len(file_response.content),
                            )
                            return cached_path
                    except Exception as exc:
                        logger.debug("Failed to download %s: %s", url, exc)

            except Exception as exc:
                logger.debug("Download page %s failed: %s", page_url, exc)

        # Strategy 3: Try API endpoint
        try:
            response = await client.get(
                CTDC_API_URL,
                params={"format": "csv", "limit": 100000},
            )
            if (
                response.status_code == 200
                and len(response.content) > 1000
                and _looks_like_csv(response.text[:2000])
            ):
                cached_path.write_bytes(response.content)
                logger.info(
                    "Downloaded CTDC dataset from API (%d bytes)",
                    len(response.content),
                )
                return cached_path
        except Exception as exc:
            logger.debug("CTDC API download failed: %s", exc)

        # Strategy 4: Use cached dataset if available
        if cached_path.exists() and cached_path.stat().st_size > 1000:
            logger.warning(
                "Could not download fresh CTDC dataset — using cached file: %s",
                cached_path,
            )
            return cached_path

        logger.error("Could not find or download CTDC dataset from any source")
        return None


def _looks_like_csv(text: str) -> bool:
    """Heuristic check: does the text look like CSV data (not HTML/JSON)?"""
    if not text:
        return False
    # CSV typically starts with header row, not < (HTML) or { (JSON)
    first_char = text.strip()[0] if text.strip() else ""
    if first_char in ("<", "{", "["):
        return False
    # Should contain commas in the first line
    first_line = text.split("\n")[0]
    return "," in first_line


def filter_pakistan_records(
    csv_path: Path, output_path: Path | None = None
) -> Path:
    """Filter CTDC dataset for Pakistan-related records.

    Searches all country-related columns for any Pakistan identifier
    (Pakistan, PAK, 586) to catch records regardless of schema version.
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed")
        return csv_path

    out_path = output_path or csv_path.parent / "ctdc_pakistan.csv"

    try:
        df = pd.read_csv(csv_path, low_memory=False)

        # Normalize column names to lowercase for consistent matching
        original_columns = list(df.columns)
        df.columns = [c.lower().strip() for c in df.columns]

        # Find country columns — broader matching than before
        country_cols = [
            c
            for c in df.columns
            if any(
                kw in c
                for kw in [
                    "country", "citizenship", "exploitation", "origin",
                    "nationality", "destination", "recruit", "transit",
                ]
            )
        ]

        if not country_cols:
            logger.warning(
                "No country columns found in CTDC dataset (columns: %s)",
                list(df.columns)[:20],
            )
            # Restore original columns before returning
            df.columns = original_columns
            return csv_path

        # Filter for Pakistan using multiple identifiers
        mask = pd.Series(False, index=df.index)
        for col in country_cols:
            col_str = df[col].astype(str).str.lower()
            for identifier in PAKISTAN_IDENTIFIERS:
                mask |= col_str.str.contains(identifier, na=False)

        pakistan_df = df[mask]

        # Restore original column names for output
        pakistan_df.columns = original_columns
        pakistan_df.to_csv(out_path, index=False)
        logger.info(
            "Filtered %d Pakistan records from %d total (searched %d country columns)",
            len(pakistan_df), len(df), len(country_cols),
        )
        return out_path

    except Exception as exc:
        logger.error("Error filtering Pakistan records: %s", exc)
        return csv_path


def parse_ctdc_records(csv_path: Path) -> list[dict[str, Any]]:
    """Parse CTDC CSV into structured records.

    Handles multiple CTDC schema versions with flexible column mapping.
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed")
        return []

    try:
        df = pd.read_csv(csv_path, low_memory=False)
        records: list[dict[str, Any]] = []

        # Normalize column names for matching
        col_lower_map = {c.lower().strip(): c for c in df.columns}

        # Standard CTDC column mappings — includes both old and new schema names
        column_map: dict[str, list[str]] = {
            "trafficking_type": [
                "typeoftrafficking", "trafficking_type", "type_trafficking",
                "traffickingtype", "type_of_trafficking",
            ],
            "exploitation_type": [
                "typeofexploitation", "exploitation_type", "type_exploitation",
                "exploitationtype", "type_of_exploitation",
            ],
            "gender": ["gender", "sex"],
            "age_group": [
                "agebroad", "age_group", "age_broad", "agegroup", "age",
            ],
            "country_of_exploitation": [
                "countryofexploitation", "country_exploitation",
                "exploitationcountry", "country_of_exploitation",
            ],
            "country_of_citizenship": [
                "citizenship", "countryofcitizenship", "nationality",
                "country_of_citizenship",
            ],
            "means_of_control": [
                "meansofcontrol", "means_control", "controlmeans",
                "means_of_control",
            ],
            "year_of_registration": [
                "yearofregistration", "year_registration", "registrationyear",
                "year_of_registration", "year",
            ],
        }

        def _resolve_column(possible_names: list[str]) -> str | None:
            """Find the actual column name from possible lowercase variants."""
            for name in possible_names:
                if name in col_lower_map:
                    return col_lower_map[name]
            return None

        # Pre-resolve column mappings once
        resolved: dict[str, str | None] = {
            target: _resolve_column(candidates)
            for target, candidates in column_map.items()
        }

        for _, row in df.iterrows():
            record: dict[str, Any] = {"source": "CTDC"}
            for target_key, actual_col in resolved.items():
                if actual_col is not None and pd.notna(row.get(actual_col)):
                    record[target_key] = str(row[actual_col])
            records.append(record)

        logger.info("Parsed %d records from CTDC CSV", len(records))
        return records

    except Exception as exc:
        logger.error("Error parsing CTDC records: %s", exc)
        return []


def compute_summary_statistics(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute summary statistics from CTDC Pakistan records."""
    summary: dict[str, Any] = {
        "total_victims": len(records),
        "by_trafficking_type": {},
        "by_gender": {},
        "by_age_group": {},
        "by_exploitation_type": {},
    }

    for record in records:
        for field, bucket in [
            ("trafficking_type", "by_trafficking_type"),
            ("gender", "by_gender"),
            ("age_group", "by_age_group"),
            ("exploitation_type", "by_exploitation_type"),
        ]:
            value = record.get(field, "unknown")
            summary[bucket][value] = summary[bucket].get(value, 0) + 1

    return summary
