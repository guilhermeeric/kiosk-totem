from src.domain.exceptions import CartNotFound
from src.domain.repositories import CartRepository


class MarkCartHandedOff:
    """Record that a session was handed off to another device via QR.

    The totem polls the cart and resets as soon as this marker is set.
    """

    def __init__(self, cart_repo: CartRepository):
        self._cart_repo = cart_repo

    async def execute(self, session_id: str) -> None:
        cart = await self._cart_repo.get_by_session_id(session_id)
        if cart is None:
            raise CartNotFound(f"Cart for session {session_id!r} not found")
        if cart.id is None:
            raise ValueError("Cart has no id; cannot be marked as handed off")
        await self._cart_repo.mark_handed_off(cart.id)
