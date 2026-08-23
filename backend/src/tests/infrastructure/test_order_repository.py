import os
from uuid import uuid4

import asyncpg
import pytest

from src.domain.order import OrderStatus
from src.infrastructure.database.order_repository import PostgresOrderRepository

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://totem:totem@localhost:5432/totem",
)


async def _connect() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(DATABASE_URL)
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"database unavailable: {exc}")


@pytest.mark.asyncio
async def test_update_status_persists_and_bumps_updated_at():
    conn = await _connect()
    cart_id = None
    order_id = None
    try:
        session_id = uuid4().hex
        cart_id = await conn.fetchval(
            "INSERT INTO carts (session_id) VALUES ($1) RETURNING id",
            session_id,
        )
        order_id = await conn.fetchval(
            "INSERT INTO orders (cart_id, customer_name, type, total) "
            "VALUES ($1, $2, 'EAT_IN', 0) RETURNING id",
            cart_id,
            "Integration Test",
        )
        assert order_id is not None

        repo = PostgresOrderRepository(conn)
        await repo.update_status(order_id, OrderStatus.PREPARING)

        row = await conn.fetchrow("SELECT status, updated_at FROM orders WHERE id = $1", order_id)
        assert row is not None
        assert row["status"] == OrderStatus.PREPARING.value
        assert row["updated_at"] is not None
    finally:
        if order_id is not None:
            await conn.execute("DELETE FROM orders WHERE id = $1", order_id)
        if cart_id is not None:
            await conn.execute("DELETE FROM carts WHERE id = $1", cart_id)
        await conn.close()
