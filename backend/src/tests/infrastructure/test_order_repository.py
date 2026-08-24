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


@pytest.mark.asyncio
async def test_loads_aggregate_with_items_and_payments():
    """The order repo returns the whole aggregate: items AND payments loaded.

    Regression: orders used to come back with payments=[] unless a usecase
    stitched them in via a second repository.
    """
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
            "VALUES ($1, $2, 'EAT_IN', 10.00) RETURNING id",
            cart_id,
            "Integration Test",
        )
        assert order_id is not None
        item_id = await conn.fetchval("SELECT id FROM items ORDER BY id LIMIT 1")
        await conn.execute(
            "INSERT INTO order_items (order_id, item_id, quantity, unit_price) "
            "VALUES ($1, $2, 1, 10.00)",
            order_id,
            item_id,
        )
        await conn.execute(
            "INSERT INTO payments (order_id, method, status) VALUES ($1, 'PIX', 'PAID')",
            order_id,
        )

        repo = PostgresOrderRepository(conn)
        order = await repo.get_by_id(order_id)
        assert order is not None
        assert [oi.item_id for oi in order.items] == [item_id]
        assert len(order.payments) == 1
        assert order.payments[0].method.value == "PIX"
        assert order.payments[0].status.value == "PAID"
        assert order.payments[0].order_id == order_id

        listed = await repo.list_by_status(OrderStatus.PENDING)
        listed_order = next(o for o in listed if o.id == order_id)
        assert len(listed_order.payments) == 1
    finally:
        if order_id is not None:
            await conn.execute("DELETE FROM payments WHERE order_id = $1", order_id)
            await conn.execute("DELETE FROM order_items WHERE order_id = $1", order_id)
            await conn.execute("DELETE FROM orders WHERE id = $1", order_id)
        if cart_id is not None:
            await conn.execute("DELETE FROM carts WHERE id = $1", cart_id)
        await conn.close()


@pytest.mark.asyncio
async def test_update_status_raises_when_order_missing():
    """Consistency: 0 affected rows must raise, like every other repo method."""
    conn = await _connect()
    try:
        repo = PostgresOrderRepository(conn)
        with pytest.raises(ValueError, match="not found"):
            await repo.update_status(999_999_999, OrderStatus.PREPARING)
    finally:
        await conn.close()
