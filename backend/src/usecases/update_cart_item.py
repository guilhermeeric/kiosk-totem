from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound
from src.domain.repositories import CartRepository


class UpdateCartItem:
    """Change the quantity of an item in a cart (0 removes the item)."""

    def __init__(self, cart_repo: CartRepository):
        self._cart_repo = cart_repo

    async def execute(self, session_id: str, item_id: int, quantity: int) -> Cart:
        cart = await self._cart_repo.get_by_session_id(session_id)
        if cart is None:
            raise CartNotFound(f"Cart for session {session_id!r} not found")

        cart.update_quantity(item_id, quantity)
        await self._cart_repo.update(cart)
        return cart
