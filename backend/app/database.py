"""Async SQLAlchemy engine and session factory."""

import ssl
from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _fix_asyncpg_url(url: str) -> tuple[str, dict]:
    """Strip sslmode from URL and return connect_args for asyncpg SSL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    needs_ssl = False
    if "sslmode" in params:
        sslmode = params.pop("sslmode")[0]
        needs_ssl = sslmode in ("require", "verify-ca", "verify-full", "prefer")

    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=new_query))

    connect_args: dict = {}
    if needs_ssl:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

    return clean_url, connect_args


_db_url = settings.database_url
_is_sqlite = _db_url.startswith("sqlite")

if _is_sqlite:
    engine = create_async_engine(_db_url, echo=False)
else:
    _clean_url, _connect_args = _fix_asyncpg_url(_db_url)
    engine = create_async_engine(
        _clean_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args=_connect_args,
    )

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        yield session
