import os
from uuid import uuid4

import asyncpg
import pytest

from src.infrastructure.database.cart_repository import PostgresCartRepository

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://totem:totem@localhost:5432/totem",
)


async def _connect() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(DATABASE_URL)
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"database unavailable: {exc}")


async def test_mark_handed_off_sets_timestamp_and_is_one_way():
    conn = await _connect()
    cart_id = None
    try:
        session_id = uuid4().hex
        cart_id = await conn.fetchval(
            "INSERT INTO carts (session_id) VALUES ($1) RETURNING id",
            session_id,
        )
        assert cart_id is not None

        repo = PostgresCartRepository(conn)
        await repo.mark_handed_off(cart_id)

        cart = await repo.get_by_session_id(session_id)
        assert cart is not None
        assert cart.handed_off_at is not None

        # One-way latch: a session can be handed off at most once. Without
        # this, a phone could "continue on phone" recursively and wipe the
        # previous device's session.
        with pytest.raises(ValueError, match="already handed off"):
            await repo.mark_handed_off(cart_id)
    finally:
        if cart_id is not None:
            await conn.execute("DELETE FROM carts WHERE id = $1", cart_id)
        await conn.close()
