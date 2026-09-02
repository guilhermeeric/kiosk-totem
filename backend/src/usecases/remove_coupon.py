from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound
from src.domain.repositories import UnitOfWork


class RemoveCoupon:
    """Detach the applied coupon from a cart (clears code and snapshot)."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def execute(self, session_id: str) -> Cart:
        async with self._uow as uow:
            cart = await uow.carts.get_by_session_id(session_id)
            if cart is None:
                raise CartNotFound(f"Cart for session {session_id!r} not found")

            cart.remove_coupon()
            await uow.carts.update(cart)
            return cart
