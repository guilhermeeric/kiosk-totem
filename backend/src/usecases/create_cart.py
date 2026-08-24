from src.domain.cart import Cart
from src.domain.repositories import UnitOfWork


class CreateCart:
    """Create a new empty cart for a session."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def execute(self, session_id: str) -> Cart:
        async with self._uow as uow:
            cart = Cart(session_id=session_id)
            await uow.carts.create(cart)
            return cart
