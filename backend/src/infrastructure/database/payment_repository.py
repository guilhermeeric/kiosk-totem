import asyncpg

from src.domain.payment import Payment, PaymentMethod, PaymentStatus
from src.domain.repositories import PaymentRepository


def payment_from_row(row: asyncpg.Record) -> Payment:
    """Hydrate a Payment from a payments row (shared by payment and order adapters)."""
    return Payment(
        id=row["id"],
        order_id=row["order_id"],
        method=PaymentMethod(row["method"]),
        status=PaymentStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresPaymentRepository(PaymentRepository):
    """PostgreSQL implementation of the PaymentRepository interface."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def create(self, payment: Payment) -> None:
        """Insert a new payment attempt. Payment.id must be None.

        A partial unique index allows at most one PAID attempt per order; a
        duplicate insert raises ValueError like the other repos.
        """
        if payment.id is not None:
            raise ValueError("Cannot create a payment with an existing ID.")

        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO payments (order_id, method, status)
                VALUES ($1, $2, $3)
                RETURNING id, order_id, method, status, created_at, updated_at
                """,
                payment.order_id,
                payment.method.value,
                payment.status.value,
            )
        except asyncpg.UniqueViolationError:
            raise ValueError("Payment could not be created") from None

        if row is None:
            raise ValueError("Payment insert returned no row")
        # Hydrate the persisted row so the returned payment reflects what is
        # stored, not just what was sent.
        hydrated = payment_from_row(row)
        payment.id = hydrated.id
        payment.method = hydrated.method
        payment.status = hydrated.status
        payment.created_at = hydrated.created_at
        payment.updated_at = hydrated.updated_at
