from src.domain.exceptions import OrderNotFound
from src.domain.order import Order
from src.domain.repositories import OrderRepository, PaymentRepository


class GetOrder:
    """Retrieve an order with its payment attempts (receipt)."""

    def __init__(self, order_repo: OrderRepository, payment_repo: PaymentRepository):
        self._order_repo = order_repo
        self._payment_repo = payment_repo

    async def execute(self, order_id: int) -> Order:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFound(f"Order {order_id} not found")
        if order.id is None:
            raise ValueError("Loaded order has no id")

        order.payments = await self._payment_repo.list_by_order(order.id)
        return order
