"""CTDC Global Synthetic Dataset downloader.

Source: https://www.ctdatacollaborative.org
Output: data/raw/ctdc/
Priority: P1
"""

from pathlib import Path
from typing import Any

import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RAW_CTDC_DIR = Path("data/raw/ctdc")
CTDC_DOWNLOAD_URL: str = (
    "https://www.ctdatacollaborative.org/download-global-dataset"
)


async def download_ctdc_dataset(
    output_dir: Path = RAW_CTDC_DIR,
) -> Path | None:
    """Download the CTDC Global Synthetic Dataset CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(
        timeout=120.0, follow_redirects=True,
        headers={"User-Agent": "Nigehbaan-DataPipeline/1.0"},
    ) as client:
        try:
            # Navigate to download page
            response = await client.get(CTDC_DOWNLOAD_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Find CSV download link
            csv_links: list[str] = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.lower().endswith(".csv") or "download" in href.lower():
                    full_url = href if href.startswith("http") else f"https://www.ctdatacollaborative.org{href}"
                    csv_links.append(full_url)

            # Also check for form-based downloads
            for form in soup.find_all("form"):
                action = form.get("action", "")
                if "download" in action.lower():
                    full_url = action if action.startswith("http") else f"https://www.ctdatacollaborative.org{action}"
                    csv_links.append(full_url)

            for url in csv_links:
                try:
                    file_response = await client.get(url)
                    if file_response.status_code == 200 and len(file_response.content) > 1000:
                        filename = "ctdc_global_synthetic.csv"
                        file_path = output_dir / filename
                        file_path.write_bytes(file_response.content)
                        logger.info("Downloaded CTDC dataset: %s (%d bytes)", file_path, len(file_response.content))
                        return file_path
                except Exception as exc:
                    logger.warning("Failed to download %s: %s", url, exc)

            logger.warning("Could not find CTDC download link")
            return None

        except Exception as exc:
            logger.error("Error downloading CTDC dataset: %s", exc)
            return None


def filter_pakistan_records(
    csv_path: Path, output_path: Path | None = None
) -> Path:
    """Filter CTDC dataset for Pakistan-related records."""
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed")
        return csv_path

    out_path = output_path or csv_path.parent / "ctdc_pakistan.csv"

    try:
        df = pd.read_csv(csv_path, low_memory=False)

        # Find country columns
        country_cols = [
            c for c in df.columns
            if any(kw in c.lower() for kw in ["country", "citizenship", "exploitation", "origin"])
        ]

        if not country_cols:
            logger.warning("No country columns found in CTDC dataset")
            return csv_path

        # Filter for Pakistan
        mask = pd.Series(False, index=df.index)
        for col in country_cols:
            mask |= df[col].astype(str).str.lower().str.contains("pakistan", na=False)

        pakistan_df = df[mask]
        pakistan_df.to_csv(out_path, index=False)
        logger.info(
            "Filtered %d Pakistan records from %d total",
            len(pakistan_df), len(df),
        )
        return out_path

    except Exception as exc:
        logger.error("Error filtering Pakistan records: %s", exc)
        return csv_path


def parse_ctdc_records(csv_path: Path) -> list[dict[str, Any]]:
    """Parse CTDC CSV into structured records."""
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed")
        return []

    try:
        df = pd.read_csv(csv_path, low_memory=False)
        records: list[dict[str, Any]] = []

        # Standard CTDC column mappings
        column_map = {
            "trafficking_type": ["typeOfTrafficking", "trafficking_type", "type_trafficking"],
            "exploitation_type": ["typeOfExploitation", "exploitation_type", "type_exploitation"],
            "gender": ["gender", "Gender"],
            "age_group": ["ageBroad", "age_group", "age_broad"],
            "country_of_exploitation": ["CountryOfExploitation", "country_exploitation"],
            "country_of_citizenship": ["citizenship", "Citizenship"],
            "means_of_control": ["meansOfControl", "means_control"],
            "year_of_registration": ["yearOfRegistration", "year_registration"],
        }

        for _, row in df.iterrows():
            record: dict[str, Any] = {"source": "CTDC"}
            for target_key, possible_cols in column_map.items():
                for col in possible_cols:
                    if col in df.columns and pd.notna(row.get(col)):
                        record[target_key] = str(row[col])
                        break
            records.append(record)

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
