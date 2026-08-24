from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound
from src.domain.repositories import UnitOfWork


class UpdateCartItem:
    """Change the quantity of an item in a cart (0 removes the item)."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def execute(self, session_id: str, item_id: int, quantity: int) -> Cart:
        async with self._uow as uow:
            cart = await uow.carts.get_by_session_id(session_id)
            if cart is None:
                raise CartNotFound(f"Cart for session {session_id!r} not found")

            cart.update_quantity(item_id, quantity)
            await uow.carts.update(cart)
            return cart
