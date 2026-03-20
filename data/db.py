"""Shared async database connection for the data pipeline.

Reads DATABASE_URL from backend/.env and provides an async session
factory for use by loaders and other pipeline scripts.
"""

import os
import ssl
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Load .env from backend directory
_env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(_env_path)

_database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/nigehbaan")


def _fix_asyncpg_url(url: str) -> tuple[str, dict]:
    """Strip sslmode from URL and return connect_args for asyncpg SSL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    needs_ssl = False
    if "sslmode" in params:
        sslmode = params.pop("sslmode")[0]
        needs_ssl = sslmode in ("require", "verify-ca", "verify-full", "prefer")

    # Rebuild URL without sslmode
    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=new_query))

    connect_args = {}
    if needs_ssl:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

    return clean_url, connect_args


_clean_url, _connect_args = _fix_asyncpg_url(_database_url)

engine = create_async_engine(
    _clean_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
