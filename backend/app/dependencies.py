"""FastAPI dependency injection providers."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, rolling back on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    # In production this would decode a JWT from the Authorization header.
    # For now it returns a placeholder dict.
) -> dict[str, Any]:
    """Placeholder dependency for authenticated user extraction.

    Replace with real JWT / session-based auth before production use.
    """
    # TODO: Implement real authentication
    return {
        "id": 0,
        "username": "anonymous",
        "role": "viewer",
    }
