from src.domain.exceptions import OrderNotFound
from src.domain.order import Order, OrderStatus
from src.domain.repositories import OrderRepository


class TransitionOrderStatus:
    """Advance an order through the status machine (PENDING → PREPARING → READY → COMPLETED).

    Illegal transitions raise ValueError via the domain machine's guards.
    """

    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo

    async def execute(self, order_id: int, new_status: OrderStatus) -> Order:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFound(f"Order {order_id} not found")
        if order.id is None:
            raise ValueError("Order has no id; status cannot be updated")

        if new_status == OrderStatus.PREPARING:
            order.mark_preparing()
        elif new_status == OrderStatus.READY:
            order.mark_ready()
        elif new_status == OrderStatus.COMPLETED:
            order.mark_completed()
        elif new_status == OrderStatus.CANCELLED:
            order.cancel()
        else:
            raise ValueError(f"Cannot transition to {new_status.value}")

        await self._order_repo.update_status(order.id, new_status)
        return order
