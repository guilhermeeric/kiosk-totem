from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound, ItemNotFound
from src.domain.repositories import CartRepository, ItemRepository


class AddCartItem:
    """Add an item to a cart (merging quantity if it is already present)."""

    def __init__(self, cart_repo: CartRepository, item_repo: ItemRepository):
        self._cart_repo = cart_repo
        self._item_repo = item_repo

    async def execute(self, session_id: str, item_id: int, quantity: int) -> Cart:
        cart = await self._cart_repo.get_by_session_id(session_id)
        if cart is None:
            raise CartNotFound(f"Cart for session {session_id!r} not found")

        item = await self._item_repo.get_by_id(item_id)
        if item is None:
            raise ItemNotFound(f"Item {item_id} not found")

        cart.add_item(item, quantity)
        await self._cart_repo.update(cart)
        return cart
