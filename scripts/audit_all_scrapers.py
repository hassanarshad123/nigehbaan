"""Audit all scrapers: run each with a timeout and produce a status report.

Usage: python -m scripts.audit_all_scrapers
   or: python scripts/audit_all_scrapers.py

Outputs:
  - Markdown table to stdout
  - SCRAPER_AUDIT_LIVE.md in the project root
"""

import asyncio
import importlib
import logging
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so `data.scrapers.*` imports work
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from run_scraper import SCRAPERS  # noqa: E402

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 120

# Status sort order: FAIL first, TIMEOUT second, PASS last
_STATUS_ORDER = {"FAIL": 0, "TIMEOUT": 1, "PASS": 2}


@dataclass
class AuditResult:
    name: str
    status: str  # PASS | FAIL | TIMEOUT
    record_count: int
    error: str
    duration: float


def _run_async(coro):
    """Run an async coroutine safely, matching the pattern in scraping_tasks.py."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _audit_one(name: str, module_path: str, class_name: str) -> AuditResult:
    """Run a single scraper with a timeout and return its result."""
    start = time.monotonic()

    # --- Import ---
    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
    except Exception as exc:
        duration = time.monotonic() - start
        return AuditResult(
            name=name,
            status="FAIL",
            record_count=0,
            error=f"ImportError: {exc}",
            duration=round(duration, 2),
        )

    # --- Run with timeout ---
    try:
        scraper = cls()
        results = await asyncio.wait_for(scraper.run(), timeout=TIMEOUT_SECONDS)
        duration = time.monotonic() - start
        record_count = len(results) if isinstance(results, list) else 0
        return AuditResult(
            name=name,
            status="PASS",
            record_count=record_count,
            error="",
            duration=round(duration, 2),
        )
    except asyncio.TimeoutError:
        duration = time.monotonic() - start
        return AuditResult(
            name=name,
            status="TIMEOUT",
            record_count=0,
            error=f"Exceeded {TIMEOUT_SECONDS}s timeout",
            duration=round(duration, 2),
        )
    except Exception as exc:
        duration = time.monotonic() - start
        short_tb = traceback.format_exception_only(type(exc), exc)
        return AuditResult(
            name=name,
            status="FAIL",
            record_count=0,
            error=short_tb[-1].strip() if short_tb else str(exc),
            duration=round(duration, 2),
        )


def _sort_results(results: list[AuditResult]) -> list[AuditResult]:
    """Sort: FAIL first, TIMEOUT second, PASS last; alphabetical within each group."""
    return sorted(results, key=lambda r: (_STATUS_ORDER.get(r.status, 99), r.name))


def _build_markdown(results: list[AuditResult]) -> str:
    """Build the full markdown report string."""
    total = len(results)
    pass_count = sum(1 for r in results if r.status == "PASS")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    timeout_count = sum(1 for r in results if r.status == "TIMEOUT")
    pass_rate = (pass_count / total * 100) if total else 0.0

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# Scraper Audit Report",
        "",
        f"Generated: **{now}**",
        "",
        "| # | Scraper | Status | Records | Duration (s) | Error |",
        "|---|---------|--------|--------:|-------------:|-------|",
    ]

    for idx, r in enumerate(results, 1):
        status_icon = {"PASS": "PASS", "FAIL": "FAIL", "TIMEOUT": "TIMEOUT"}[r.status]
        error_cell = r.error.replace("|", "\\|") if r.error else ""
        lines.append(
            f"| {idx} | {r.name} | {status_icon} | {r.record_count} | {r.duration} | {error_cell} |"
        )

    lines.extend([
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Total scrapers | {total} |",
        f"| PASS | {pass_count} |",
        f"| FAIL | {fail_count} |",
        f"| TIMEOUT | {timeout_count} |",
        f"| Pass rate | {pass_rate:.1f}% |",
        "",
    ])

    return "\n".join(lines)


async def audit_all() -> list[AuditResult]:
    """Run every scraper sequentially and collect results."""
    results: list[AuditResult] = []
    total = len(SCRAPERS)

    for idx, (name, (module_path, class_name)) in enumerate(SCRAPERS.items(), 1):
        print(f"[{idx}/{total}] Auditing {name} ...", end=" ", flush=True)
        result = await _audit_one(name, module_path, class_name)
        print(f"{result.status} ({result.duration}s)")
        results.append(result)

    return _sort_results(results)


def main() -> None:
    results = _run_async(audit_all())

    md = _build_markdown(results)

    # Write to file
    out_path = PROJECT_ROOT / "SCRAPER_AUDIT_LIVE.md"
    out_path.write_text(md, encoding="utf-8")

    # Print to stdout
    print("\n" + "=" * 70)
    print(md)
    print("=" * 70)
    print(f"\nReport written to {out_path}")


if __name__ == "__main__":
    main()
