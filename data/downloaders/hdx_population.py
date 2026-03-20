"""HDX COD-PS population estimates downloader.

Downloads the Common Operational Dataset for Population Statistics
(COD-PS) from HDX. Provides population estimates with P-codes
aligned to the COD-AB administrative boundaries.

Source: https://data.humdata.org/dataset/cod-ps-pak
Output: data/raw/population/
Schedule: One-time download (annual updates)
Priority: P0 — Foundation population data with P-code alignment
"""

from pathlib import Path
from typing import Any

import logging
import re

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

RAW_POPULATION_DIR = Path("data/raw/population")

HDX_DATASET_ID: str = "cod-ps-pak"
HDX_API_URL: str = (
    f"https://data.humdata.org/api/3/action/package_show?id={HDX_DATASET_ID}"
)

# Column name patterns for identifying key fields
_PCODE_PATTERNS: list[str] = [
    r"adm\d+_pcode",
    r"admin\d+_pcode",
    r"adm\d+pcode",
    r"pcode",
    r"p_code",
    r"hzcode",
]

_NAME_PATTERNS: list[str] = [
    r"adm\d+_name",
    r"admin\d+_name",
    r"adm\d+name",
    r"name",
    r"admin_name",
    r"area_name",
]

_POPULATION_PATTERNS: list[str] = [
    r"t_tl",
    r"total",
    r"pop_total",
    r"population",
    r"both_sexes",
    r"t_m",
    r"male",
    r"pop_male",
    r"t_f",
    r"female",
    r"pop_female",
]


def _find_column(df: pd.DataFrame, patterns: list[str]) -> str | None:
    """Find the first column in df matching any of the regex patterns.

    Args:
        df: DataFrame to search.
        patterns: List of regex patterns to match column names.

    Returns:
        Matching column name or None.
    """
    for pattern in patterns:
        for col in df.columns:
            if re.search(pattern, col.lower().strip()):
                return col
    return None


def _detect_admin_level(columns: list[str]) -> int | None:
    """Detect admin level from column names.

    Args:
        columns: List of column names.

    Returns:
        Detected admin level (1, 2, or 3) or None.
    """
    cols_lower = [c.lower() for c in columns]
    for level in [3, 2, 1]:
        for col in cols_lower:
            if f"adm{level}" in col or f"admin{level}" in col:
                return level
    return None


async def download_population_estimates(
    output_dir: Path = RAW_POPULATION_DIR,
) -> dict[str, Path]:
    """Download HDX COD-PS population estimate files.

    Downloads Excel/CSV files with population estimates at
    admin levels 1-3, aligned with COD-AB P-codes.

    Args:
        output_dir: Directory to save downloaded files.

    Returns:
        Dict mapping admin level to downloaded file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: dict[str, Path] = {}

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(60.0),
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Nigehbaan-DataPipeline/1.0 "
                "(Anti-Trafficking Research; +https://nigehbaan.pk)"
            ),
        },
    ) as client:
        # Fetch dataset metadata
        logger.info("Fetching HDX COD-PS dataset metadata from %s", HDX_API_URL)
        try:
            response = await client.get(HDX_API_URL)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch HDX COD-PS metadata: %s", exc)
            return downloaded

        payload = response.json()
        if not payload.get("success"):
            logger.error("HDX API returned unsuccessful response for COD-PS")
            return downloaded

        resources = payload.get("result", {}).get("resources", [])
        if not resources:
            logger.error("No resources found in HDX COD-PS dataset")
            return downloaded

        # Download all population data resources (CSV, Excel)
        for resource in resources:
            url = resource.get("url", "")
            name = resource.get("name", "") or resource.get("description", "")
            fmt = (resource.get("format", "") or "").lower()

            # Accept CSV and Excel formats
            is_data_file = fmt in (
                "csv",
                "xlsx",
                "xls",
                "excel",
            ) or any(
                url.lower().endswith(ext)
                for ext in (".csv", ".xlsx", ".xls")
            )
            if not is_data_file:
                continue

            # Determine file extension from URL or format
            if url.lower().endswith(".csv") or fmt == "csv":
                ext = ".csv"
            else:
                ext = ".xlsx"

            # Create a safe filename
            safe_name = re.sub(r"[^\w\-.]", "_", name)[:80] if name else "population"
            file_name = f"{safe_name}{ext}"
            file_path = output_dir / file_name

            logger.info("Downloading population resource: %s -> %s", name, file_path)
            try:
                dl_response = await client.get(url)
                dl_response.raise_for_status()
                file_path.write_bytes(dl_response.content)

                # Determine the admin level key for this file
                level_key = _detect_admin_level_from_name(name) or file_name
                downloaded[level_key] = file_path
                logger.info(
                    "Downloaded population file: %s (%d bytes)",
                    file_path,
                    len(dl_response.content),
                )
            except httpx.HTTPError as exc:
                logger.error(
                    "Failed to download population resource %s: %s", name, exc
                )

    logger.info("HDX population download complete: %d files", len(downloaded))
    return downloaded


def _detect_admin_level_from_name(name: str) -> str | None:
    """Detect admin level key from a resource name string.

    Args:
        name: Resource name to inspect.

    Returns:
        Key like 'adm1', 'adm2', 'adm3' or None.
    """
    name_lower = name.lower()
    for level in [3, 2, 1, 0]:
        patterns = [f"adm{level}", f"admin{level}", f"level{level}", f"level_{level}"]
        for pattern in patterns:
            if pattern in name_lower:
                return f"adm{level}"
    return None


def parse_population_csv(csv_path: Path) -> list[dict[str, Any]]:
    """Parse HDX population CSV into structured records.

    Extracts population estimates by admin unit with P-code
    alignment for spatial joins.

    Args:
        csv_path: Path to the population CSV/Excel file.

    Returns:
        List of population records with pcode, name,
        admin_level, population_total, population_male,
        population_female, year fields.
    """
    if not csv_path.exists():
        logger.error("Population file not found: %s", csv_path)
        return []

    # Read the file based on extension
    try:
        suffix = csv_path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(csv_path, encoding="utf-8", dtype=str)
        elif suffix in (".xlsx", ".xls"):
            # Try reading the first sheet; some files have multiple sheets
            xls = pd.ExcelFile(csv_path)
            # Prefer sheets with 'pop' or 'adm' in the name
            target_sheet = None
            for sheet_name in xls.sheet_names:
                sheet_lower = sheet_name.lower()
                if any(kw in sheet_lower for kw in ("pop", "adm", "data", "estimate")):
                    target_sheet = sheet_name
                    break
            if target_sheet is None and xls.sheet_names:
                target_sheet = xls.sheet_names[0]
            df = pd.read_excel(csv_path, sheet_name=target_sheet, dtype=str)
        else:
            logger.error("Unsupported file format: %s", suffix)
            return []
    except Exception as exc:
        logger.error("Failed to read population file %s: %s", csv_path, exc)
        return []

    if df.empty:
        logger.warning("Empty DataFrame from %s", csv_path)
        return []

    # Detect admin level from columns
    admin_level = _detect_admin_level(list(df.columns))

    # Find key columns
    pcode_col = _find_column(df, _PCODE_PATTERNS)
    name_col = _find_column(df, _NAME_PATTERNS)

    # Find population columns
    total_col = _find_column(df, [r"t_tl", r"total", r"pop_total", r"population", r"both_sexes"])
    male_col = _find_column(df, [r"t_m", r"male", r"pop_male", r"male_total"])
    female_col = _find_column(df, [r"t_f", r"female", r"pop_female", r"female_total"])

    # Find year column
    year_col = _find_column(df, [r"year", r"ref_year", r"data_year", r"estimate_year"])

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        pcode = str(row[pcode_col]).strip() if pcode_col and pd.notna(row.get(pcode_col)) else ""
        name = str(row[name_col]).strip() if name_col and pd.notna(row.get(name_col)) else ""

        # Skip rows without a meaningful identifier
        if not pcode and not name:
            continue

        # Parse population values (remove commas, convert to int)
        pop_total = _parse_int(row.get(total_col)) if total_col else None
        pop_male = _parse_int(row.get(male_col)) if male_col else None
        pop_female = _parse_int(row.get(female_col)) if female_col else None
        year = str(row[year_col]).strip() if year_col and pd.notna(row.get(year_col)) else None

        records.append({
            "pcode": pcode,
            "name": name,
            "admin_level": admin_level,
            "population_total": pop_total,
            "population_male": pop_male,
            "population_female": pop_female,
            "year": year,
        })

    logger.info(
        "Parsed %d population records from %s (admin level %s)",
        len(records),
        csv_path,
        admin_level,
    )
    return records


def _parse_int(value: Any) -> int | None:
    """Safely parse a value to int, handling commas and NaN.

    Args:
        value: The value to parse.

    Returns:
        Integer value or None if unparseable.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        cleaned = str(value).replace(",", "").replace(" ", "").strip()
        if not cleaned or cleaned.lower() in ("nan", "none", "", "-"):
            return None
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def build_pcode_population_map(
    records: list[dict[str, Any]],
) -> dict[str, int]:
    """Build a P-code to total population mapping.

    Args:
        records: List of parsed population records.

    Returns:
        Dict mapping P-code to total population.
    """
    pcode_map: dict[str, int] = {}
    for record in records:
        pcode = record.get("pcode", "")
        pop_total = record.get("population_total")

        if not pcode:
            continue

        if pop_total is not None:
            # If pcode already exists, keep the larger value
            # (handles cases where multiple rows exist for same area)
            if pcode in pcode_map:
                pcode_map[pcode] = max(pcode_map[pcode], pop_total)
            else:
                pcode_map[pcode] = pop_total

    logger.info("Built pcode->population map with %d entries", len(pcode_map))
    return pcode_map


def get_dataset_metadata() -> dict[str, Any]:
    """Fetch HDX COD-PS dataset metadata.

    Returns:
        Dict with dataset info including last_modified date.
    """
    try:
        with httpx.Client(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Nigehbaan-DataPipeline/1.0 "
                    "(Anti-Trafficking Research; +https://nigehbaan.pk)"
                ),
            },
        ) as client:
            response = client.get(HDX_API_URL)
            response.raise_for_status()

        payload = response.json()
        if not payload.get("success"):
            logger.error("HDX API returned unsuccessful response for COD-PS")
            return {}

        result = payload.get("result", {})
        resources = result.get("resources", [])

        return {
            "name": result.get("name", ""),
            "title": result.get("title", ""),
            "last_modified": result.get("metadata_modified", ""),
            "resource_count": len(resources),
            "resources": [
                {
                    "name": r.get("name", ""),
                    "format": r.get("format", ""),
                    "url": r.get("url", ""),
                    "size": r.get("size"),
                    "last_modified": r.get("last_modified", ""),
                }
                for r in resources
            ],
        }
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch HDX COD-PS metadata: %s", exc)
        return {}
