from src.domain.cart import Cart
from src.domain.repositories import CartRepository


class CreateCart:
    """Create a new empty cart for a session."""

    def __init__(self, cart_repo: CartRepository):
        self._cart_repo = cart_repo

    async def execute(self, session_id: str) -> Cart:
        cart = Cart(session_id=session_id)
        await self._cart_repo.create(cart)
        return cart
