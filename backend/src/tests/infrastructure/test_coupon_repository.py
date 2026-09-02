import os
from uuid import uuid4

import asyncpg
import pytest

from src.infrastructure.database.coupon_repository import PostgresCouponRepository

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://totem:totem@localhost:5432/totem",
)


async def _connect() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(DATABASE_URL)
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"database unavailable: {exc}")


async def _insert_coupon(conn: asyncpg.Connection, quantity: int, code: str | None = None) -> str:
    coupon_code = code or f"TEST{uuid4().hex[:8].upper()}"
    await conn.execute(
        "INSERT INTO coupons (coupon_code, total_discount, expiry_time, quantity) "
        "VALUES ($1, 1.00, CURRENT_TIMESTAMP + INTERVAL '1 day', $2)",
        coupon_code,
        quantity,
    )
    return coupon_code


async def test_get_by_code_returns_entity_with_all_fields():
    conn = await _connect()
    code = None
    try:
        code = await _insert_coupon(conn, 7)
        repo = PostgresCouponRepository(conn)

        coupon = await repo.get_by_code(code)

        assert coupon is not None
        assert coupon.coupon_code == code
        assert coupon.total_discount == pytest.approx(1.00)
        assert coupon.quantity == 7
        assert coupon.expiry_time is not None
        assert coupon.created_at is not None
    finally:
        if code is not None:
            await conn.execute("DELETE FROM coupons WHERE coupon_code = $1", code)
        await conn.close()


async def test_get_by_code_unknown_returns_none():
    conn = await _connect()
    try:
        repo = PostgresCouponRepository(conn)
        assert await repo.get_by_code("NO-SUCH-CODE") is None
    finally:
        await conn.close()


async def test_consume_decrements_quantity():
    conn = await _connect()
    code = None
    try:
        code = await _insert_coupon(conn, 2)
        repo = PostgresCouponRepository(conn)

        await repo.consume(code)

        quantity = await conn.fetchval("SELECT quantity FROM coupons WHERE coupon_code = $1", code)
        assert quantity == 1
    finally:
        if code is not None:
            await conn.execute("DELETE FROM coupons WHERE coupon_code = $1", code)
        await conn.close()


async def test_consume_last_use_can_only_be_consumed_once():
    conn = await _connect()
    code = None
    try:
        code = await _insert_coupon(conn, 1)
        repo = PostgresCouponRepository(conn)

        await repo.consume(code)
        with pytest.raises(ValueError, match="no remaining uses"):
            await repo.consume(code)

        quantity = await conn.fetchval("SELECT quantity FROM coupons WHERE coupon_code = $1", code)
        assert quantity == 0
    finally:
        if code is not None:
            await conn.execute("DELETE FROM coupons WHERE coupon_code = $1", code)
        await conn.close()


async def test_consume_unknown_code_raises():
    conn = await _connect()
    try:
        repo = PostgresCouponRepository(conn)
        with pytest.raises(ValueError, match="not found"):
            await repo.consume("NO-SUCH-CODE")
    finally:
        await conn.close()
