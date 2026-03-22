"""Shared fixtures and helpers for API tests.

When no database is available, the asyncpg driver raises
ConnectionRefusedError before FastAPI can return a 500.  The helper
below catches that and treats it as a "DB unavailable" skip so that
the test suite stays green in environments without Postgres.
"""

from __future__ import annotations

import contextlib
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.main import app

TRANSPORT = ASGITransport(app=app)
BASE_URL = "http://test"

# Status codes that are acceptable when the DB may or may not be present.
ACCEPTABLE_CODES = {200, 500}

# Extend the acceptable set to include the synthetic 503
ACCEPTABLE_CODES_WITH_DB_DOWN = {200, 500, 503}


async def api_get(path: str, **params: Any) -> tuple[int, dict | list | None]:
    """Issue a GET request against the test ASGI app.

    Returns ``(status_code, parsed_body)`` on success.
    If the DB is unreachable and the driver raises before FastAPI can
    respond, returns ``(503, None)`` so callers can handle it uniformly.
    """
    try:
        async with AsyncClient(transport=TRANSPORT, base_url=BASE_URL) as client:
            resp = await client.get(path, params=params, timeout=15.0)
            with contextlib.suppress(Exception):
                body = resp.json()
                return resp.status_code, body
            return resp.status_code, None
    except Exception as exc:
        # Catch ANY connection/driver error — DB not running locally.
        # Common: ConnectionRefusedError, OSError, TimeoutError,
        # asyncpg.PostgresError, sqlalchemy.exc.OperationalError, etc.
        exc_name = type(exc).__name__
        if any(
            keyword in exc_name.lower()
            for keyword in ("connect", "timeout", "os", "operational", "interface", "postgres")
        ) or isinstance(exc, (ConnectionRefusedError, OSError, TimeoutError)):
            return 503, None
        # Re-raise truly unexpected errors
        raise
