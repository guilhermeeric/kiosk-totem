from decimal import Decimal
from unittest.mock import AsyncMock

from src.domain.order import Order, OrderStatus, OrderType
from src.domain.repositories import OrderRepository
from src.usecases.list_orders import ListOrders


async def test_list_orders_delegates_by_status():
    order_repo = AsyncMock(spec=OrderRepository)
    orders = [
        Order(
            id=1,
            cart_id=1,
            customer_name="Alice",
            order_type=OrderType.EAT_IN,
            items=[],
            total=Decimal("5.00"),
            status=OrderStatus.PENDING,
        ),
        Order(
            id=2,
            cart_id=2,
            customer_name="Bob",
            order_type=OrderType.TAKEAWAY,
            items=[],
            total=Decimal("3.50"),
            status=OrderStatus.PENDING,
        ),
    ]
    order_repo.list_by_status.return_value = orders

    result = await ListOrders(order_repo).execute(OrderStatus.PENDING)

    assert result == orders
    order_repo.list_by_status.assert_called_once_with(OrderStatus.PENDING)
