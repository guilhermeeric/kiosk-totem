from src.domain.exceptions import CartNotFound
from src.domain.order import Order, OrderItem, OrderType
from src.domain.repositories import CartRepository, OrderRepository


class Checkout:
    """Convert a cart into an order and consume the cart."""

    def __init__(self, cart_repo: CartRepository, order_repo: OrderRepository):
        self._cart_repo = cart_repo
        self._order_repo = order_repo

    async def execute(self, session_id: str, customer_name: str, order_type: OrderType) -> Order:
        cart = await self._cart_repo.get_by_session_id(session_id)
        if cart is None:
            raise CartNotFound(f"Cart for session {session_id!r} not found")
        if cart.is_empty():
            raise ValueError("Cannot checkout an empty cart")
        if cart.id is None:
            raise ValueError("Cart has no id; cannot be checked out")

        order = Order(
            cart_id=cart.id,
            customer_name=customer_name,
            order_type=order_type,
            items=[
                OrderItem(
                    item_id=ci.item_id,
                    quantity=ci.quantity,
                    unit_price=ci.unit_price,
                )
                for ci in cart.items
            ],
            total=cart.total(),
        )

        await self._order_repo.create(order)
        return order
