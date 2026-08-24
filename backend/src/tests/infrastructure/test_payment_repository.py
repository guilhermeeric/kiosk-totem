import os
from unittest.mock import AsyncMock
from uuid import uuid4

import asyncpg
import pytest

from src.domain.payment import Payment, PaymentMethod, PaymentStatus
from src.infrastructure.database.payment_repository import PostgresPaymentRepository

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://totem:totem@localhost:5432/totem",
)


async def _connect() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(DATABASE_URL)
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"database unavailable: {exc}")


async def test_create_payment_roundtrips():
    """Regression: INSERT ... RETURNING must include method/status so the
    persisted row hydrates (first attempt used to raise KeyError: 'method')."""
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

        repo = PostgresPaymentRepository(conn)

        payment = Payment(order_id=order_id, method=PaymentMethod.PIX)
        payment.mark_paid()
        await repo.create(payment)

        assert payment.id is not None
        assert payment.method == PaymentMethod.PIX
        assert payment.status == PaymentStatus.PAID
    finally:
        if order_id is not None:
            await conn.execute("DELETE FROM payments WHERE order_id = $1", order_id)
            await conn.execute("DELETE FROM orders WHERE id = $1", order_id)
        if cart_id is not None:
            await conn.execute("DELETE FROM carts WHERE id = $1", cart_id)
        await conn.close()


async def test_one_paid_attempt_per_order_rejects_a_second_paid_row():
    """The partial unique index (one_paid_attempt_per_order) is the DB-level
    guarantee that a payment can never be recorded twice."""
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

        await conn.execute(
            "INSERT INTO payments (order_id, method, status) VALUES ($1, 'PIX', 'PAID')",
            order_id,
        )
        with pytest.raises(asyncpg.UniqueViolationError):
            await conn.execute(
                "INSERT INTO payments (order_id, method, status) VALUES ($1, 'PIX', 'PAID')",
                order_id,
            )
    finally:
        if order_id is not None:
            await conn.execute("DELETE FROM payments WHERE order_id = $1", order_id)
            await conn.execute("DELETE FROM orders WHERE id = $1", order_id)
        if cart_id is not None:
            await conn.execute("DELETE FROM carts WHERE id = $1", cart_id)
        await conn.close()


async def test_create_translates_unique_violation_to_value_error():
    """Contract: a DB unique violation must never escape as a 500. The repo
    raises ValueError like the cart/order repos do."""
    conn = AsyncMock()
    conn.fetchrow.side_effect = [asyncpg.UniqueViolationError]
    repo = PostgresPaymentRepository(conn)

    payment = Payment(order_id=1, method=PaymentMethod.PIX)
    payment.mark_paid()

    with pytest.raises(ValueError):
        await repo.create(payment)
