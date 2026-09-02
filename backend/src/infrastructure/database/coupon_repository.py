import asyncpg

from src.domain.coupon import Coupon
from src.domain.repositories import CouponRepository


class PostgresCouponRepository(CouponRepository):
    """PostgreSQL implementation of the CouponRepository interface."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def get_by_code(self, coupon_code: str) -> Coupon | None:
        row = await self._conn.fetchrow(
            "SELECT coupon_code, percent, expiry_time, quantity, "
            "created_at, updated_at FROM coupons WHERE coupon_code = $1",
            coupon_code,
        )
        if not row:
            return None
        return Coupon(
            coupon_code=row["coupon_code"],
            discount_percent=row["percent"],
            expiry_time=row["expiry_time"],
            quantity=row["quantity"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def consume(self, coupon_code: str) -> None:
        # FOR UPDATE: within the checkout transaction this row-locks the coupon
        # so concurrent redemptions serialize — exactly one can take the last
        # use; the loser reads the decremented quantity and fails the check.
        # Only the paid checkout calls this, so a row can never be missing here
        # (the cart FK guarantees the coupon exists); defensive ValueError anyway.
        row = await self._conn.fetchrow(
            "SELECT quantity FROM coupons WHERE coupon_code = $1 FOR UPDATE",
            coupon_code,
        )
        if row is None:
            raise ValueError(f"Coupon {coupon_code!r} not found")
        if row["quantity"] <= 0:
            raise ValueError(f"Coupon {coupon_code!r} has no remaining uses")
        await self._conn.execute(
            "UPDATE coupons SET quantity = quantity - 1 WHERE coupon_code = $1",
            coupon_code,
        )
