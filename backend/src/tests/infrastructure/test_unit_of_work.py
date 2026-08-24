import os
from uuid import uuid4

import asyncpg
import pytest

from src.domain.cart import Cart
from src.infrastructure.database.unit_of_work import PostgresUnitOfWork

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://totem:totem@localhost:5432/totem",
)


async def _connect() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(DATABASE_URL)
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"database unavailable: {exc}")


async def test_commits_on_clean_exit():
    conn = await _connect()
    session_id = uuid4().hex
    try:
        async with PostgresUnitOfWork(conn) as uow:
            cart = Cart(session_id=session_id)
            await uow.carts.create(cart)
            cart_id = cart.id

        row = await conn.fetchval("SELECT id FROM carts WHERE session_id = $1", session_id)
        assert row == cart_id
    finally:
        await conn.execute("DELETE FROM carts WHERE session_id = $1", session_id)
        await conn.close()


async def test_rolls_back_on_exception():
    conn = await _connect()
    session_id = uuid4().hex
    try:
        with pytest.raises(ValueError):
            async with PostgresUnitOfWork(conn) as uow:
                cart = Cart(session_id=session_id)
                await uow.carts.create(cart)
                raise ValueError("boom")

        row = await conn.fetchval("SELECT id FROM carts WHERE session_id = $1", session_id)
        assert row is None
    finally:
        await conn.execute("DELETE FROM carts WHERE session_id = $1", session_id)
        await conn.close()
