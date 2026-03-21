"""Scraper Health Monitor — runs all scrapers and generates a health report.

Usage:
    python scripts/scraper_monitor.py

Outputs:
    - SCRAPER_HEALTH.md  (project root)
    - data/scraper_health_history.json  (append per run)
    - Updates data_sources table if DB is available
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path so imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from run_scraper import SCRAPERS  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("scraper_monitor")

HEALTH_REPORT_PATH = PROJECT_ROOT / "SCRAPER_HEALTH.md"
HISTORY_PATH = PROJECT_ROOT / "data" / "scraper_health_history.json"
SCRAPER_TIMEOUT = 120.0  # seconds per scraper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_history() -> list[dict]:
    """Load existing run history from disk (returns empty list on error)."""
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(history: list[dict]) -> None:
    """Persist run history to disk."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(
        json.dumps(history, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


def _classify_error(error_str: str) -> str:
    """Classify an error string into a short category."""
    lower = error_str.lower()
    if "timeout" in lower or "timed out" in lower:
        return "TIMEOUT"
    if "403" in lower or "forbidden" in lower or "waf" in lower:
        return "403/WAF"
    if "404" in lower or "not found" in lower:
        return "404"
    if "connection" in lower or "connect" in lower:
        return "CONNECTION"
    if "ssl" in lower or "certificate" in lower:
        return "SSL"
    return "OTHER"


def _consecutive_failures(scraper_name: str, history: list[dict]) -> int:
    """Count how many consecutive recent runs this scraper has failed."""
    count = 0
    for run in reversed(history):
        results_map = {r["name"]: r for r in run.get("results", [])}
        entry = results_map.get(scraper_name)
        if entry is None:
            break
        if entry.get("status") != "pass":
            count += 1
        else:
            break
    return count


# ---------------------------------------------------------------------------
# Run a single scraper with timeout
# ---------------------------------------------------------------------------

async def _run_single_scraper(name: str) -> dict:
    """Run a single scraper, returning a result dict."""
    module_path, class_name = SCRAPERS[name]
    start = time.monotonic()
    try:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        scraper = cls()

        results = await asyncio.wait_for(scraper.run(), timeout=SCRAPER_TIMEOUT)
        elapsed = round(time.monotonic() - start, 2)

        return {
            "name": name,
            "status": "pass",
            "record_count": len(results),
            "error": None,
            "error_category": None,
            "duration_s": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except asyncio.TimeoutError:
        elapsed = round(time.monotonic() - start, 2)
        return {
            "name": name,
            "status": "fail",
            "record_count": 0,
            "error": f"Timed out after {SCRAPER_TIMEOUT}s",
            "error_category": "TIMEOUT",
            "duration_s": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        elapsed = round(time.monotonic() - start, 2)
        error_str = f"{type(exc).__name__}: {exc}"
        return {
            "name": name,
            "status": "fail",
            "record_count": 0,
            "error": error_str,
            "error_category": _classify_error(error_str),
            "duration_s": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Database update (best-effort)
# ---------------------------------------------------------------------------

async def _try_update_db(results: list[dict]) -> bool:
    """Try to update the data_sources table. Returns True on success."""
    try:
        from backend.app.database import async_session_factory  # noqa: WPS433
        from backend.app.models.news_articles import DataSource  # noqa: WPS433
        from sqlalchemy import update  # noqa: WPS433

        async with async_session_factory() as session:
            for entry in results:
                stmt = (
                    update(DataSource)
                    .where(DataSource.scraper_name == entry["name"])
                    .values(
                        last_scraped=datetime.now(timezone.utc),
                        record_count=entry["record_count"],
                        is_active=(entry["status"] == "pass"),
                    )
                )
                await session.execute(stmt)
            await session.commit()
        logger.info("data_sources table updated for %d scrapers.", len(results))
        return True
    except Exception as exc:
        logger.warning("Skipping DB update: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def _generate_markdown(
    results: list[dict],
    run_ts: str,
    history: list[dict],
) -> str:
    """Build the SCRAPER_HEALTH.md content."""

    # Sort: failures first, then alphabetical
    sorted_results = sorted(results, key=lambda r: (r["status"] == "pass", r["name"]))

    passed = [r for r in results if r["status"] == "pass"]
    failed = [r for r in results if r["status"] != "pass"]
    total_records = sum(r["record_count"] for r in results)
    avg_duration = (
        round(sum(r["duration_s"] for r in results) / len(results), 2)
        if results
        else 0
    )

    lines = [
        "# Scraper Health Report",
        "",
        f"**Generated:** {run_ts}  ",
        f"**Total scrapers:** {len(results)}  ",
        f"**Passed:** {len(passed)} | **Failed:** {len(failed)}  ",
        f"**Total records:** {total_records}  ",
        f"**Avg duration:** {avg_duration}s",
        "",
        "## Results",
        "",
        "| # | Scraper | Status | Records | Duration | Error |",
        "|---|---------|--------|---------|----------|-------|",
    ]

    for i, r in enumerate(sorted_results, 1):
        status_icon = "PASS" if r["status"] == "pass" else "FAIL"
        error_col = r.get("error") or ""
        # Truncate long errors for readability
        if len(error_col) > 80:
            error_col = error_col[:77] + "..."
        lines.append(
            f"| {i} | {r['name']} | {status_icon} | {r['record_count']} "
            f"| {r['duration_s']}s | {error_col} |"
        )

    # --- Summary by error category ---
    if failed:
        category_counts: dict[str, int] = {}
        for r in failed:
            cat = r.get("error_category") or "UNKNOWN"
            category_counts[cat] = category_counts.get(cat, 0) + 1
        lines.extend([
            "",
            "## Failure Breakdown",
            "",
            "| Category | Count |",
            "|----------|-------|",
        ])
        for cat, cnt in sorted(category_counts.items()):
            lines.append(f"| {cat} | {cnt} |")

    # --- Trend section ---
    if len(history) >= 2:
        prev_run = history[-2]
        prev_results_map = {r["name"]: r for r in prev_run.get("results", [])}
        new_failures: list[str] = []
        new_recoveries: list[str] = []

        for r in results:
            prev = prev_results_map.get(r["name"])
            if prev is None:
                continue
            if r["status"] != "pass" and prev.get("status") == "pass":
                new_failures.append(r["name"])
            elif r["status"] == "pass" and prev.get("status") != "pass":
                new_recoveries.append(r["name"])

        lines.extend(["", "## Trend (vs previous run)", ""])
        if new_failures:
            lines.append(f"**Newly failing ({len(new_failures)}):** " + ", ".join(new_failures))
        if new_recoveries:
            lines.append(f"**Recovered ({len(new_recoveries)}):** " + ", ".join(new_recoveries))
        if not new_failures and not new_recoveries:
            lines.append("No status changes since last run.")

    # --- Chronic failures (3+ consecutive) ---
    chronic: list[tuple[str, int]] = []
    for r in results:
        consec = _consecutive_failures(r["name"], history)
        if consec >= 3:
            chronic.append((r["name"], consec))

    if chronic:
        chronic.sort(key=lambda t: -t[1])
        lines.extend([
            "",
            "## Chronic Failures (3+ consecutive)",
            "",
            "| Scraper | Consecutive Failures |",
            "|---------|---------------------|",
        ])
        for name, count in chronic:
            lines.append(f"| {name} | {count} |")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_monitor() -> list[dict]:
    """Execute all scrapers and produce reports. Returns results list."""
    run_ts = datetime.now(timezone.utc).isoformat()
    logger.info("Starting scraper health check at %s", run_ts)
    logger.info("Running %d scrapers with %ds timeout each", len(SCRAPERS), int(SCRAPER_TIMEOUT))

    results: list[dict] = []
    for name in SCRAPERS:
        logger.info("Running: %s", name)
        result = await _run_single_scraper(name)
        status_label = "PASS" if result["status"] == "pass" else "FAIL"
        logger.info(
            "  %s — %s — %d records in %ss",
            name, status_label, result["record_count"], result["duration_s"],
        )
        if result["error"]:
            logger.info("  Error: %s", result["error"])
        results.append(result)

    # --- Load history and append current run ---
    history = _load_history()
    current_run = {
        "timestamp": run_ts,
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "pass"),
        "failed": sum(1 for r in results if r["status"] != "pass"),
        "results": results,
    }
    history.append(current_run)
    _save_history(history)
    logger.info("History saved to %s (%d runs total)", HISTORY_PATH, len(history))

    # --- Generate markdown report ---
    md_content = _generate_markdown(results, run_ts, history)
    HEALTH_REPORT_PATH.write_text(md_content, encoding="utf-8")
    logger.info("Health report written to %s", HEALTH_REPORT_PATH)

    # --- Try DB update (best-effort) ---
    await _try_update_db(results)

    # --- Print summary ---
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = len(results) - passed
    logger.info("Done: %d passed, %d failed out of %d scrapers", passed, failed, len(results))

    return results


if __name__ == "__main__":
    asyncio.run(run_monitor())
