import os
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


@pytest.mark.asyncio
async def test_create_payment_roundtrips_and_is_idempotent_for_paid():
    """Regression: INSERT ... RETURNING must include method/status so the
    persisted row hydrates (first attempt used to raise KeyError: 'method').
    A retry after a successful PAID insert must return the stored payment."""
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
        first_id = payment.id

        retry = Payment(order_id=order_id, method=PaymentMethod.PIX)
        retry.mark_paid()
        await repo.create(retry)

        assert retry.id == first_id
        rows = await conn.fetch("SELECT id FROM payments WHERE order_id = $1", order_id)
        assert len(rows) == 1
    finally:
        if order_id is not None:
            await conn.execute("DELETE FROM payments WHERE order_id = $1", order_id)
            await conn.execute("DELETE FROM orders WHERE id = $1", order_id)
        if cart_id is not None:
            await conn.execute("DELETE FROM carts WHERE id = $1", cart_id)
        await conn.close()
