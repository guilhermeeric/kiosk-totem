from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.exceptions import OrderNotFound
from src.domain.order import Order, OrderType
from src.domain.payment import Payment, PaymentMethod, PaymentStatus
from src.domain.repositories import OrderRepository
from src.usecases.get_order import GetOrder


@pytest.mark.asyncio
async def test_get_order_returns_aggregate_with_payments():
    """The order repo loads the whole aggregate; GetOrder no longer stitches payments."""
    order_repo = AsyncMock(spec=OrderRepository)
    order = Order(
        id=42,
        cart_id=3,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("23.48"),
    )
    order.payments = [
        Payment(id=1, order_id=42, method=PaymentMethod.PIX, status=PaymentStatus.PAID),
    ]
    order_repo.get_by_id.return_value = order

    result = await GetOrder(order_repo).execute(42)

    assert result is order
    assert result.payments == order.payments
    order_repo.get_by_id.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_get_order_raises_when_missing():
    order_repo = AsyncMock(spec=OrderRepository)
    order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFound, match="42"):
        await GetOrder(order_repo).execute(42)
