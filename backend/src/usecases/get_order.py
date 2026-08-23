from src.domain.exceptions import OrderNotFound
from src.domain.order import Order
from src.domain.repositories import OrderRepository


class GetOrder:
    """Retrieve an order with its payment attempts (receipt)."""

    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo

    async def execute(self, order_id: int) -> Order:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFound(f"Order {order_id} not found")
        return order
