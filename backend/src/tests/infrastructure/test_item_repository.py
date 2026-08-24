import os
from uuid import uuid4

import asyncpg
import pytest

from src.domain.exceptions import ItemNotFound
from src.infrastructure.database.item_repository import PostgresItemRepository

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://totem:totem@localhost:5432/totem",
)


async def _connect() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(DATABASE_URL)
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"database unavailable: {exc}")


async def _insert_item(conn: asyncpg.Connection, stock: int) -> int:
    item_id = await conn.fetchval(
        "INSERT INTO items (name, price, category, stock) "
        "VALUES ($1, 1.00, 'test', $2) RETURNING id",
        f"stock-test-{uuid4().hex[:8]}",
        stock,
    )
    assert item_id is not None
    return item_id


async def test_consume_stock_decrements():
    conn = await _connect()
    item_id = None
    try:
        item_id = await _insert_item(conn, 20)
        repo = PostgresItemRepository(conn)

        await repo.consume_stock(item_id, 3)

        stock = await conn.fetchval("SELECT stock FROM items WHERE id = $1", item_id)
        assert stock == 17
    finally:
        if item_id is not None:
            await conn.execute("DELETE FROM items WHERE id = $1", item_id)
        await conn.close()


async def test_consume_stock_rejects_quantity_above_available():
    conn = await _connect()
    item_id = None
    try:
        item_id = await _insert_item(conn, 2)
        repo = PostgresItemRepository(conn)

        with pytest.raises(ValueError, match="Only 2 left"):
            await repo.consume_stock(item_id, 3)

        # Nothing consumed.
        stock = await conn.fetchval("SELECT stock FROM items WHERE id = $1", item_id)
        assert stock == 2
    finally:
        if item_id is not None:
            await conn.execute("DELETE FROM items WHERE id = $1", item_id)
        await conn.close()


async def test_consume_stock_last_unit_can_only_be_consumed_once():
    conn = await _connect()
    item_id = None
    try:
        item_id = await _insert_item(conn, 1)
        repo = PostgresItemRepository(conn)

        await repo.consume_stock(item_id, 1)
        with pytest.raises(ValueError, match="Only 0 left"):
            await repo.consume_stock(item_id, 1)

        stock = await conn.fetchval("SELECT stock FROM items WHERE id = $1", item_id)
        assert stock == 0
    finally:
        if item_id is not None:
            await conn.execute("DELETE FROM items WHERE id = $1", item_id)
        await conn.close()


async def test_consume_stock_unknown_item_raises_not_found():
    conn = await _connect()
    try:
        repo = PostgresItemRepository(conn)
        with pytest.raises(ItemNotFound):
            await repo.consume_stock(999_999_999, 1)
    finally:
        await conn.close()
