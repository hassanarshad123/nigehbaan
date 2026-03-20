"""Pakistan Census 2017 data downloader.

Clones the CERP Analytics PBS 2017 GitHub repository which
contains parsed CSV files from the Pakistan Bureau of Statistics
2017 census. Provides district-level population data.

Source: https://github.com/cerp-analytics/pbs2017
Output: data/raw/census/
Schedule: One-time download
Priority: P0 — Foundation population data for per-capita calculations
"""

from pathlib import Path
from typing import Any

import asyncio
import logging
import subprocess

import pandas as pd

logger = logging.getLogger(__name__)

RAW_CENSUS_DIR = Path("data/raw/census")

GITHUB_REPO_URL: str = "https://github.com/cerp-analytics/pbs2017.git"

# Common column name mappings across different census CSV formats
_DISTRICT_PATTERNS: list[str] = [
    "district",
    "admin_unit",
    "administrative_unit",
    "area",
    "name",
]

_PROVINCE_PATTERNS: list[str] = [
    "province",
    "region",
    "division",
]

_POPULATION_PATTERNS: list[str] = [
    "population",
    "total",
    "pop",
    "persons",
    "both_sexes",
    "all",
]

_MALE_PATTERNS: list[str] = [
    "male",
    "men",
    "boys",
    "m_pop",
]

_FEMALE_PATTERNS: list[str] = [
    "female",
    "women",
    "girls",
    "f_pop",
]


def _find_col(df: pd.DataFrame, patterns: list[str]) -> str | None:
    """Find first column matching any pattern (case-insensitive).

    Args:
        df: DataFrame to search.
        patterns: Substrings to match.

    Returns:
        Column name or None.
    """
    for pattern in patterns:
        for col in df.columns:
            if pattern in col.lower().strip():
                return col
    return None


async def clone_census_repo(
    output_dir: Path = RAW_CENSUS_DIR,
) -> Path | None:
    """Clone the CERP Analytics PBS 2017 repository.

    The repository contains parsed CSV files from the Pakistan
    Bureau of Statistics 2017 census with district-level
    population breakdowns.

    Args:
        output_dir: Directory to clone into.

    Returns:
        Path to the cloned repository, or None on failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = output_dir / "pbs2017"

    try:
        if repo_dir.exists() and (repo_dir / ".git").exists():
            # Repository already cloned — pull latest
            logger.info("Census repo already exists at %s, pulling latest", repo_dir)
            process = await asyncio.create_subprocess_exec(
                "git",
                "pull",
                "--ff-only",
                cwd=str(repo_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.warning(
                    "git pull failed (returncode=%d): %s",
                    process.returncode,
                    stderr.decode("utf-8", errors="replace"),
                )
                # Even if pull fails, the existing clone is still usable
                logger.info("Using existing clone despite pull failure")
            else:
                logger.info(
                    "git pull succeeded: %s",
                    stdout.decode("utf-8", errors="replace").strip(),
                )
            return repo_dir

        # Fresh clone
        logger.info("Cloning census repo from %s to %s", GITHUB_REPO_URL, repo_dir)
        process = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "1",
            GITHUB_REPO_URL,
            str(repo_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            logger.error("git clone failed (returncode=%d): %s", process.returncode, error_msg)
            return None

        logger.info("Successfully cloned census repo to %s", repo_dir)

        # Verify clone success
        if not (repo_dir / ".git").exists():
            logger.error("Clone directory exists but .git not found: %s", repo_dir)
            return None

        return repo_dir

    except FileNotFoundError:
        logger.error(
            "git is not installed or not in PATH. "
            "Install git to clone the census repository."
        )
        return None
    except Exception as exc:
        logger.error("Unexpected error cloning census repo: %s", exc)
        return None


def discover_csv_files(repo_dir: Path) -> list[Path]:
    """Find all CSV files in the cloned census repository.

    Args:
        repo_dir: Path to the cloned repository.

    Returns:
        List of paths to CSV files.
    """
    if not repo_dir.exists():
        logger.warning("Census repo directory does not exist: %s", repo_dir)
        return []

    csv_files = sorted(repo_dir.rglob("*.csv"))
    logger.info("Discovered %d CSV files in %s", len(csv_files), repo_dir)
    return csv_files


def parse_district_population(csv_path: Path) -> list[dict[str, Any]]:
    """Parse a census CSV file for district-level population data.

    Extracts population counts by district, gender, and
    urban/rural classification.

    Args:
        csv_path: Path to a census CSV file.

    Returns:
        List of population records with district, province,
        gender, urban_rural, population fields.
    """
    if not csv_path.exists():
        logger.error("Census CSV file not found: %s", csv_path)
        return []

    # Try multiple encodings common in Pakistani data
    df = None
    for encoding in ("utf-8", "latin-1", "cp1252", "utf-8-sig"):
        try:
            df = pd.read_csv(csv_path, encoding=encoding, dtype=str)
            break
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
        except Exception as exc:
            logger.warning("Error reading %s with %s: %s", csv_path, encoding, exc)
            continue

    if df is None or df.empty:
        logger.warning("Could not read or empty CSV: %s", csv_path)
        return []

    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]

    # Find relevant columns
    district_col = _find_col(df, _DISTRICT_PATTERNS)
    province_col = _find_col(df, _PROVINCE_PATTERNS)
    pop_col = _find_col(df, _POPULATION_PATTERNS)
    male_col = _find_col(df, _MALE_PATTERNS)
    female_col = _find_col(df, _FEMALE_PATTERNS)

    # Detect urban/rural column
    urban_rural_col = _find_col(df, ["urban", "rural", "area_type", "classification"])

    # If no population-related columns found, skip this file
    if not district_col and not pop_col:
        logger.debug(
            "No district or population columns found in %s (columns: %s)",
            csv_path,
            list(df.columns),
        )
        return []

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        district = (
            str(row[district_col]).strip()
            if district_col and pd.notna(row.get(district_col))
            else ""
        )
        province = (
            str(row[province_col]).strip()
            if province_col and pd.notna(row.get(province_col))
            else ""
        )
        population = _safe_int(row.get(pop_col)) if pop_col else None
        male = _safe_int(row.get(male_col)) if male_col else None
        female = _safe_int(row.get(female_col)) if female_col else None
        urban_rural = (
            str(row[urban_rural_col]).strip()
            if urban_rural_col and pd.notna(row.get(urban_rural_col))
            else ""
        )

        # Skip rows without useful data
        if not district and population is None:
            continue

        records.append({
            "district": district,
            "province": province,
            "population": population,
            "male": male,
            "female": female,
            "urban_rural": urban_rural,
            "source_file": csv_path.name,
        })

    logger.info(
        "Parsed %d district-population records from %s",
        len(records),
        csv_path.name,
    )
    return records


def _safe_int(value: Any) -> int | None:
    """Safely convert a value to int, handling commas and NaN.

    Args:
        value: Value to convert.

    Returns:
        Integer or None.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        cleaned = str(value).replace(",", "").replace(" ", "").strip()
        if not cleaned or cleaned.lower() in ("nan", "none", "-", ""):
            return None
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def parse_all_census_data(
    repo_dir: Path,
) -> dict[str, list[dict[str, Any]]]:
    """Parse all census CSV files into structured data.

    Args:
        repo_dir: Path to the cloned census repository.

    Returns:
        Dict mapping table names to their parsed records.
    """
    csv_files = discover_csv_files(repo_dir)
    all_data: dict[str, list[dict[str, Any]]] = {}

    for csv_path in csv_files:
        # Use the file stem (without extension) as the table name
        table_name = csv_path.stem.lower().strip()

        records = parse_district_population(csv_path)
        if records:
            all_data[table_name] = records
            logger.info("Table '%s': %d records", table_name, len(records))
        else:
            logger.debug("Table '%s': no parseable records", table_name)

    logger.info(
        "Parsed %d census tables with data from %d CSV files",
        len(all_data),
        len(csv_files),
    )
    return all_data


def build_district_lookup(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build a district lookup table from census data.

    Creates a mapping from district name to its population
    data for use in per-capita calculations.

    Args:
        records: List of parsed population records.

    Returns:
        Dict mapping district name to population data.
    """
    lookup: dict[str, dict[str, Any]] = {}

    for record in records:
        district = record.get("district", "").strip()
        if not district:
            continue

        # Normalize district name to lowercase for consistent lookups
        district_key = district.lower()

        if district_key not in lookup:
            lookup[district_key] = {
                "district": district,
                "province": record.get("province", ""),
                "total": 0,
                "male": 0,
                "female": 0,
                "urban": 0,
                "rural": 0,
            }

        entry = lookup[district_key]

        population = record.get("population")
        male = record.get("male")
        female = record.get("female")
        urban_rural = record.get("urban_rural", "").lower()

        # Update province if not yet set
        if not entry["province"] and record.get("province"):
            entry = {**entry, "province": record["province"]}
            lookup[district_key] = entry

        # Aggregate population counts
        if population is not None:
            if "urban" in urban_rural:
                lookup[district_key] = {
                    **entry,
                    "urban": entry["urban"] + population,
                    "total": entry["total"] + population,
                }
            elif "rural" in urban_rural:
                lookup[district_key] = {
                    **entry,
                    "rural": entry["rural"] + population,
                    "total": entry["total"] + population,
                }
            else:
                # If no urban/rural classification, treat as total
                # Only add if total hasn't been set by classified rows
                if entry["urban"] == 0 and entry["rural"] == 0:
                    lookup[district_key] = {
                        **entry,
                        "total": max(entry["total"], population),
                    }

        if male is not None:
            lookup[district_key] = {
                **lookup[district_key],
                "male": lookup[district_key]["male"] + male,
            }

        if female is not None:
            lookup[district_key] = {
                **lookup[district_key],
                "female": lookup[district_key]["female"] + female,
            }

    logger.info("Built district lookup with %d districts", len(lookup))
    return lookup
