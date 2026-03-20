"""Walk Free Global Slavery Index data downloader.

Source: https://www.walkfree.org/global-slavery-index/
Output: data/raw/gsi/
Priority: P2
"""

from pathlib import Path
from typing import Any

import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RAW_GSI_DIR = Path("data/raw/gsi")
GSI_URL: str = "https://www.walkfree.org/global-slavery-index/"

VULNERABILITY_INDICATORS: list[str] = [
    "governance_issues", "lack_of_basic_needs", "inequality",
    "disenfranchised_groups", "effects_of_conflict", "civil_liberties",
    "political_instability", "regulatory_quality", "rule_of_law",
    "corruption", "government_response", "criminal_justice",
    "coordination_and_accountability", "national_action_plan",
    "shelter_services", "risk_assessment", "supply_chain_transparency",
    "international_cooperation", "worker_protections",
    "attitudes_and_social_systems", "displaced_populations",
    "internet_access", "women_insecurity",
]


async def download_gsi_data(
    output_dir: Path = RAW_GSI_DIR,
) -> Path | None:
    """Download Walk Free GSI data for Pakistan."""
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(
        timeout=60.0, follow_redirects=True,
        headers={"User-Agent": "Nigehbaan-DataPipeline/1.0"},
    ) as client:
        try:
            response = await client.get(GSI_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Look for download links (Excel/CSV)
            download_links: list[str] = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if any(ext in href.lower() for ext in [".xlsx", ".csv", ".xls", "download"]):
                    full_url = href if href.startswith("http") else f"https://www.walkfree.org{href}"
                    download_links.append(full_url)

            if not download_links:
                # Try the data/map page
                map_response = await client.get(f"{GSI_URL}map/")
                map_soup = BeautifulSoup(map_response.text, "lxml")
                for link in map_soup.find_all("a", href=True):
                    href = link["href"]
                    if any(ext in href.lower() for ext in [".xlsx", ".csv", ".xls"]):
                        full_url = href if href.startswith("http") else f"https://www.walkfree.org{href}"
                        download_links.append(full_url)

            for url in download_links:
                try:
                    file_response = await client.get(url)
                    file_response.raise_for_status()
                    filename = Path(url).name or "gsi_data.xlsx"
                    file_path = output_dir / filename
                    file_path.write_bytes(file_response.content)
                    logger.info("Downloaded GSI data: %s (%d bytes)", file_path, len(file_response.content))
                    return file_path
                except Exception as exc:
                    logger.warning("Failed to download %s: %s", url, exc)

            # Fallback: save the HTML page itself for manual extraction
            html_path = output_dir / "gsi_page.html"
            html_path.write_text(response.text, encoding="utf-8")
            logger.info("Saved GSI page HTML for manual extraction: %s", html_path)
            return html_path

        except Exception as exc:
            logger.error("Error downloading GSI data: %s", exc)
            return None


def extract_pakistan_row(file_path: Path) -> dict[str, Any]:
    """Extract Pakistan's row from the GSI dataset."""
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed")
        return {}

    result: dict[str, Any] = {"country": "Pakistan"}
    try:
        if file_path.suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        else:
            return result

        # Find Pakistan row (case-insensitive)
        country_cols = [c for c in df.columns if "country" in c.lower() or "name" in c.lower()]
        for col in country_cols:
            mask = df[col].astype(str).str.lower() == "pakistan"
            if mask.any():
                pak_row = df[mask].iloc[0]
                result.update(pak_row.to_dict())
                break

    except Exception as exc:
        logger.error("Error extracting Pakistan row: %s", exc)

    return result


def parse_vulnerability_indicators(
    pakistan_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Parse individual vulnerability indicators into records."""
    records: list[dict[str, Any]] = []
    for indicator in VULNERABILITY_INDICATORS:
        value = pakistan_data.get(indicator)
        if value is None:
            # Try case-insensitive match
            for key, val in pakistan_data.items():
                if indicator.replace("_", " ") in key.lower().replace("_", " "):
                    value = val
                    break

        records.append({
            "indicator_name": indicator,
            "indicator_value": value,
            "country": "Pakistan",
            "source": "Walk Free GSI",
        })

    return records


def compare_with_region(
    file_path: Path, region: str = "South Asia"
) -> dict[str, Any]:
    """Compare Pakistan's GSI scores with regional averages."""
    try:
        import pandas as pd
    except ImportError:
        return {}

    try:
        if file_path.suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        else:
            return {}

        # Find region column
        region_cols = [c for c in df.columns if "region" in c.lower()]
        if not region_cols:
            return {}

        region_col = region_cols[0]
        region_df = df[df[region_col].astype(str).str.contains(region, case=False, na=False)]

        if region_df.empty:
            return {}

        numeric_cols = region_df.select_dtypes(include="number").columns
        regional_avg = region_df[numeric_cols].mean().to_dict()

        # Get Pakistan values
        pak_data = extract_pakistan_row(file_path)

        return {
            "pakistan": pak_data,
            "regional_average": regional_avg,
            "region": region,
        }
    except Exception as exc:
        logger.error("Error comparing with region: %s", exc)
        return {}
