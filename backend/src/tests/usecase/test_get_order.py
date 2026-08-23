from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.exceptions import OrderNotFound
from src.domain.order import Order, OrderType
from src.domain.payment import Payment, PaymentMethod, PaymentStatus
from src.domain.repositories import OrderRepository, PaymentRepository
from src.usecases.get_order import GetOrder


@pytest.mark.asyncio
async def test_get_order_attaches_payment_attempts():
    order_repo = AsyncMock(spec=OrderRepository)
    payment_repo = AsyncMock(spec=PaymentRepository)
    order = Order(
        id=42,
        cart_id=3,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("23.48"),
    )
    order_repo.get_by_id.return_value = order
    attempts = [
        Payment(id=1, order_id=42, method=PaymentMethod.PIX, status=PaymentStatus.PAID),
    ]
    payment_repo.list_by_order.return_value = attempts

    use_case = GetOrder(order_repo, payment_repo)
    result = await use_case.execute(42)

    assert result.id == 42
    assert result.payments == attempts
    payment_repo.list_by_order.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_get_order_raises_when_missing():
    order_repo = AsyncMock(spec=OrderRepository)
    payment_repo = AsyncMock(spec=PaymentRepository)
    order_repo.get_by_id.return_value = None

    use_case = GetOrder(order_repo, payment_repo)
    with pytest.raises(OrderNotFound, match="42"):
        await use_case.execute(42)
