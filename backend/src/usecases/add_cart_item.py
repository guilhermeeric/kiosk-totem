from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound, ItemNotFound
from src.domain.repositories import UnitOfWork


class AddCartItem:
    """Add an item to a cart (merging quantity if it is already present)."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def execute(self, session_id: str, item_id: int, quantity: int) -> Cart:
        async with self._uow as uow:
            cart = await uow.carts.get_by_session_id(session_id)
            if cart is None:
                raise CartNotFound(f"Cart for session {session_id!r} not found")

            item = await uow.items.get_by_id(item_id)
            if item is None:
                raise ItemNotFound(f"Item {item_id} not found")

            cart.add_item(item, quantity)
            await uow.carts.update(cart)
            return cart
