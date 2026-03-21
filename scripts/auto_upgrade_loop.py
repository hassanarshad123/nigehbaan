"""Auto-Upgrade Loop — reads monitor results and applies runtime fixes.

Applies only runtime configuration changes (never modifies source code):
  - TIMEOUT  → retry with 2x timeout override
  - 403/WAF  → switch to Wayback Machine fallback URL
  - 404      → check for URL redirects via HEAD request
  - 0 results → try broadening search terms via config

Usage:
    python scripts/auto_upgrade_loop.py
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from run_scraper import SCRAPERS  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("auto_upgrade")

HISTORY_PATH = PROJECT_ROOT / "data" / "scraper_health_history.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "scraper_config.json"
LOG_PATH = PROJECT_ROOT / "data" / "auto_upgrade_log.json"

# Wayback Machine CDX API template
WAYBACK_CDX_URL = "https://web.archive.org/cdx/search/cdx"

# Extra search terms to append when a scraper returns 0 results
BROADENED_TERMS = [
    "child protection",
    "trafficking",
    "child abuse",
    "exploitation",
    "missing children",
]


# ---------------------------------------------------------------------------
# Config helpers (immutable-style: always return new dicts)
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    """Load scraper runtime config from disk."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config(config: dict) -> None:
    """Persist config to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


def _load_history() -> list[dict]:
    """Load scraper health history."""
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _load_upgrade_log() -> list[dict]:
    """Load existing auto-upgrade log entries."""
    if not LOG_PATH.exists():
        return []
    try:
        data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_upgrade_log(log_entries: list[dict]) -> None:
    """Persist upgrade log to disk."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(
        json.dumps(log_entries, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


def _get_last_run_results(history: list[dict]) -> list[dict]:
    """Extract the results list from the most recent monitor run."""
    if not history:
        return []
    last_run = history[-1]
    return last_run.get("results", [])


# ---------------------------------------------------------------------------
# Fix strategies
# ---------------------------------------------------------------------------

def _apply_timeout_fix(
    scraper_name: str, config: dict, result: dict
) -> tuple[dict, str]:
    """Double the timeout for scrapers that timed out.

    Returns a new config dict and a description of what changed.
    """
    module_path, class_name = SCRAPERS[scraper_name]
    mod = __import__(module_path, fromlist=[class_name])
    cls = getattr(mod, class_name)
    base_timeout = getattr(cls, "request_timeout", 30.0)

    scraper_cfg = config.get(scraper_name, {})
    current_timeout = scraper_cfg.get("timeout_override", base_timeout)
    new_timeout = current_timeout * 2

    # Cap at 600 seconds to prevent infinite growth
    new_timeout = min(new_timeout, 600.0)

    new_scraper_cfg = {**scraper_cfg, "timeout_override": new_timeout}
    new_config = {**config, scraper_name: new_scraper_cfg}

    desc = f"Timeout override: {current_timeout}s -> {new_timeout}s"
    return new_config, desc


async def _apply_waf_fix(
    scraper_name: str, config: dict, result: dict
) -> tuple[dict, str]:
    """Enable Wayback Machine fallback for scrapers hitting 403/WAF.

    Returns a new config dict and a description of what changed.
    """
    scraper_cfg = config.get(scraper_name, {})

    if scraper_cfg.get("wayback_fallback"):
        return config, "Wayback fallback already enabled (no change)"

    # Try to find an archived version via Wayback CDX API
    module_path, class_name = SCRAPERS[scraper_name]
    mod = __import__(module_path, fromlist=[class_name])
    cls = getattr(mod, class_name)
    source_url = getattr(cls, "source_url", "")

    wayback_available = False
    if source_url:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    WAYBACK_CDX_URL,
                    params={
                        "url": source_url,
                        "output": "json",
                        "limit": "1",
                        "fl": "timestamp,statuscode",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if len(data) > 1:  # first row is header
                        wayback_available = True
        except Exception as exc:
            logger.warning("Wayback CDX check failed for %s: %s", scraper_name, exc)

    new_scraper_cfg = {**scraper_cfg, "wayback_fallback": True}
    new_config = {**config, scraper_name: new_scraper_cfg}

    if wayback_available:
        desc = f"Wayback fallback enabled (archived copy found for {source_url})"
    else:
        desc = f"Wayback fallback enabled (no archive confirmed for {source_url})"

    return new_config, desc


async def _apply_redirect_fix(
    scraper_name: str, config: dict, result: dict
) -> tuple[dict, str]:
    """Check if a 404'd URL has a redirect, and log the finding.

    Returns a new config dict and a description of what changed.
    """
    module_path, class_name = SCRAPERS[scraper_name]
    mod = __import__(module_path, fromlist=[class_name])
    cls = getattr(mod, class_name)
    source_url = getattr(cls, "source_url", "")

    if not source_url:
        return config, "No source_url to check for redirects"

    redirect_url = None
    try:
        async with httpx.AsyncClient(
            timeout=15, follow_redirects=False
        ) as client:
            resp = await client.head(source_url)
            if resp.status_code in (301, 302, 307, 308):
                redirect_url = str(resp.headers.get("location", ""))
    except Exception as exc:
        logger.warning("Redirect check failed for %s: %s", scraper_name, exc)

    scraper_cfg = config.get(scraper_name, {})

    if redirect_url:
        new_scraper_cfg = {
            **scraper_cfg,
            "redirect_url": redirect_url,
            "notes": f"Original URL returned 404; redirects to {redirect_url}",
        }
        new_config = {**config, scraper_name: new_scraper_cfg}
        desc = f"URL redirect detected: {source_url} -> {redirect_url}"
    else:
        new_scraper_cfg = {
            **scraper_cfg,
            "notes": "404 confirmed — no redirect found; may need manual URL update",
        }
        new_config = {**config, scraper_name: new_scraper_cfg}
        desc = f"No redirect found for {source_url} (true 404)"

    return new_config, desc


def _apply_zero_results_fix(
    scraper_name: str, config: dict, result: dict
) -> tuple[dict, str]:
    """Broaden search terms for scrapers returning 0 results.

    Returns a new config dict and a description of what changed.
    """
    scraper_cfg = config.get(scraper_name, {})
    existing_terms = scraper_cfg.get("extra_search_terms", [])

    # Only add terms that aren't already present
    new_terms = [t for t in BROADENED_TERMS if t not in existing_terms]
    if not new_terms:
        return config, "All broadened search terms already applied (no change)"

    merged_terms = existing_terms + new_terms
    new_scraper_cfg = {**scraper_cfg, "extra_search_terms": merged_terms}
    new_config = {**config, scraper_name: new_scraper_cfg}

    desc = f"Added {len(new_terms)} broadened search terms: {new_terms}"
    return new_config, desc


# ---------------------------------------------------------------------------
# Retry a single scraper after fix
# ---------------------------------------------------------------------------

async def _retry_scraper(scraper_name: str, config: dict) -> dict:
    """Re-run a single failed scraper with config overrides applied.

    Returns a result dict similar to the monitor's format.
    """
    module_path, class_name = SCRAPERS[scraper_name]
    scraper_cfg = config.get(scraper_name, {})

    start = time.monotonic()
    try:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        scraper = cls()

        # Apply timeout override if present
        timeout_override = scraper_cfg.get("timeout_override")
        if timeout_override is not None:
            scraper.request_timeout = float(timeout_override)

        timeout_limit = scraper_cfg.get("timeout_override", 120.0)
        results = await asyncio.wait_for(scraper.run(), timeout=timeout_limit)
        elapsed = round(time.monotonic() - start, 2)

        return {
            "name": scraper_name,
            "status": "pass",
            "record_count": len(results),
            "error": None,
            "duration_s": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except asyncio.TimeoutError:
        elapsed = round(time.monotonic() - start, 2)
        return {
            "name": scraper_name,
            "status": "fail",
            "record_count": 0,
            "error": f"Retry timed out after {scraper_cfg.get('timeout_override', 120)}s",
            "duration_s": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        elapsed = round(time.monotonic() - start, 2)
        return {
            "name": scraper_name,
            "status": "fail",
            "record_count": 0,
            "error": f"{type(exc).__name__}: {exc}",
            "duration_s": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def run_auto_upgrade() -> list[dict]:
    """Analyze last monitor run, apply fixes, and retry failed scrapers.

    Returns the list of action log entries for this run.
    """
    run_ts = datetime.now(timezone.utc).isoformat()

    history = _load_history()
    if not history:
        logger.error("No monitor history found at %s. Run scraper_monitor.py first.", HISTORY_PATH)
        return []

    last_results = _get_last_run_results(history)
    if not last_results:
        logger.error("Last monitor run has no results. Run scraper_monitor.py first.")
        return []

    failed_results = [r for r in last_results if r["status"] != "pass"]
    if not failed_results:
        logger.info("All scrapers passed in the last run — nothing to fix.")
        return []

    logger.info(
        "Found %d failed scrapers in last run. Analyzing fixes...",
        len(failed_results),
    )

    config = _load_config()
    actions: list[dict] = []

    for result in failed_results:
        name = result["name"]
        error_category = result.get("error_category", "OTHER")

        # Skip disabled scrapers
        scraper_cfg = config.get(name, {})
        if scraper_cfg.get("disabled"):
            logger.info("Skipping %s (disabled in config)", name)
            continue

        logger.info("Analyzing: %s (category: %s)", name, error_category)
        fix_desc = ""

        # --- Apply the appropriate fix strategy ---
        if error_category == "TIMEOUT":
            config, fix_desc = _apply_timeout_fix(name, config, result)
        elif error_category == "403/WAF":
            config, fix_desc = await _apply_waf_fix(name, config, result)
        elif error_category == "404":
            config, fix_desc = await _apply_redirect_fix(name, config, result)
        elif result.get("record_count", 0) == 0 and error_category == "OTHER":
            config, fix_desc = _apply_zero_results_fix(name, config, result)
        else:
            fix_desc = f"No automatic fix available for category: {error_category}"

        logger.info("  Fix applied: %s", fix_desc)

        # --- Retry the scraper ---
        logger.info("  Retrying %s...", name)
        retry_result = await _retry_scraper(name, config)
        retry_status = "PASS" if retry_result["status"] == "pass" else "FAIL"
        logger.info(
            "  Retry result: %s — %d records in %ss",
            retry_status,
            retry_result["record_count"],
            retry_result["duration_s"],
        )
        if retry_result["error"]:
            logger.info("  Retry error: %s", retry_result["error"])

        action_entry = {
            "timestamp": run_ts,
            "scraper": name,
            "original_error": result.get("error", ""),
            "error_category": error_category,
            "fix_applied": fix_desc,
            "retry_status": retry_result["status"],
            "retry_records": retry_result["record_count"],
            "retry_error": retry_result.get("error"),
            "retry_duration_s": retry_result["duration_s"],
        }
        actions.append(action_entry)

    # --- Persist updated config ---
    _save_config(config)
    logger.info("Config saved to %s", CONFIG_PATH)

    # --- Append to upgrade log ---
    upgrade_log = _load_upgrade_log()
    upgrade_log.append({
        "timestamp": run_ts,
        "failed_count": len(failed_results),
        "actions": actions,
    })
    _save_upgrade_log(upgrade_log)
    logger.info("Upgrade log saved to %s (%d entries)", LOG_PATH, len(upgrade_log))

    # --- Summary ---
    retried = len(actions)
    recovered = sum(1 for a in actions if a["retry_status"] == "pass")
    still_failing = retried - recovered
    logger.info(
        "Auto-upgrade complete: %d retried, %d recovered, %d still failing",
        retried, recovered, still_failing,
    )

    return actions


if __name__ == "__main__":
    asyncio.run(run_auto_upgrade())
