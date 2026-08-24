import os
from collections.abc import AsyncGenerator

import asyncpg

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Create or return the global asyncpg connection pool."""
    global _pool
    if _pool is None:
        # Local dev default (docker-compose sets DATABASE_URL explicitly for
        # containers, pointing at the db service host).
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://totem:totem@localhost:5432/totem",
        )
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
    return _pool


async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency that yields a connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def close_pool() -> None:
    """Close the global connection pool (call on application shutdown)."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
