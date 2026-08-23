from src.domain.order import Order, OrderStatus
from src.domain.repositories import OrderRepository


class ListOrders:
    """List orders matching a status (kitchen columns, visor queue)."""

    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo

    async def execute(self, status: OrderStatus) -> list[Order]:
        return await self._order_repo.list_by_status(status)
