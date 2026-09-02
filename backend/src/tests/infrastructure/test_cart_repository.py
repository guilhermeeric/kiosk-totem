import os
from uuid import uuid4

import asyncpg
import pytest

from src.domain.cart import Cart
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


async def test_create_and_update_roundtrip_coupon_columns():
    conn = await _connect()
    cart_id = None
    coupon_code = None
    other_code = None
    try:
        coupon_code = f"CT{uuid4().hex[:8].upper()}"
        await conn.execute(
            "INSERT INTO coupons (coupon_code, percent, expiry_time, quantity) "
            "VALUES ($1, 5, CURRENT_TIMESTAMP + INTERVAL '1 day', 10)",
            coupon_code,
        )
        repo = PostgresCartRepository(conn)

        cart = Cart(
            session_id=uuid4().hex,
            coupon_code=coupon_code,
            coupon_percent=5,
        )
        await repo.create(cart)
        assert cart.id is not None
        cart_id = cart.id

        loaded = await repo.get_by_session_id(cart.session_id)
        assert loaded is not None
        assert loaded.coupon_code == coupon_code
        assert loaded.coupon_percent == 5

        # Update replaces the coupon (and clearing works too).
        other_code = f"CT{uuid4().hex[:8].upper()}"
        await conn.execute(
            "INSERT INTO coupons (coupon_code, percent, expiry_time, quantity) "
            "VALUES ($1, 7, CURRENT_TIMESTAMP + INTERVAL '1 day', 10)",
            other_code,
        )
        cart.coupon_code = other_code
        cart.coupon_percent = 7
        await repo.update(cart)

        loaded = await repo.get_by_session_id(cart.session_id)
        assert loaded is not None
        assert loaded.coupon_code == other_code
        assert loaded.coupon_percent == 7

        cart.remove_coupon()
        await repo.update(cart)
        loaded = await repo.get_by_session_id(cart.session_id)
        assert loaded is not None
        assert loaded.coupon_code is None
        assert loaded.coupon_percent == 0
    finally:
        if cart_id is not None:
            await conn.execute("DELETE FROM carts WHERE id = $1", cart_id)
        for code in (coupon_code, other_code):
            if code is not None:
                await conn.execute("DELETE FROM coupons WHERE coupon_code = $1", code)
        await conn.close()
