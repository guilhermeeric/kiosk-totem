from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .cart import Cart


@dataclass(frozen=True)
class Coupon:
    """Operator-issued discount code. Application rules live here, not in usecases."""

    coupon_code: str
    total_discount: Decimal
    expiry_time: datetime
    quantity: int  # remaining paid redemptions; decremented per paid order
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def add(self, cart: Cart, now: datetime) -> None:
        """Attach this coupon to a cart if still usable at `now`; else refuse.

        The single deep entry for applying: the applicability gates (not
        expired, uses left) and the snapshot attach happen here, so the
        usecase never checks validity itself. `now` is injected to keep the
        rule pure and testable; the usecase passes `datetime.now()`. The cart
        snapshots total_discount verbatim — a coupon value edited later never
        changes what an applied cart charges. Quantity is only gated here;
        the authoritative decrement happens at paid checkout (consume).
        """
        if now >= self.expiry_time:
            raise ValueError(f"Coupon {self.coupon_code!r} expired at {self.expiry_time}")
        if self.quantity <= 0:
            raise ValueError(f"Coupon {self.coupon_code!r} has no remaining uses")
        cart.apply_coupon(self.coupon_code, self.total_discount)
