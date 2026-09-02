from datetime import datetime

from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound, CouponNotFound
from src.domain.repositories import UnitOfWork


class ApplyCoupon:
    """Attach a coupon to a cart, snapshotted at apply time.

    Thin by design: the only concern here is existence (404). Expiry, the
    uses-left gate, and the snapshot attach are Coupon.add's job — the deep
    entry that owns the rules. Once applied the value is locked; checkout
    honors it without re-reading the coupon (see Checkout).
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def execute(self, session_id: str, coupon_code: str) -> Cart:
        async with self._uow as uow:
            cart = await uow.carts.get_by_session_id(session_id)
            if cart is None:
                raise CartNotFound(f"Cart for session {session_id!r} not found")

            coupon = await uow.coupons.get_by_code(coupon_code)
            if coupon is None:
                raise CouponNotFound(f"Coupon code {coupon_code!r} not found")

            coupon.add(cart, datetime.now())  # applicability gates + snapshot attach, one call
            await uow.carts.update(cart)
            return cart
