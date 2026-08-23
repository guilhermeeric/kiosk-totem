from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.exceptions import OrderNotFound
from src.domain.order import Order, OrderStatus, OrderType
from src.domain.repositories import OrderRepository
from src.usecases.transition_order_status import TransitionOrderStatus


def _pending_order(order_id: int = 42) -> Order:
    return Order(
        id=order_id,
        cart_id=3,
        customer_name="Alice",
        order_type=OrderType.EAT_IN,
        items=[],
        total=Decimal("5.00"),
        status=OrderStatus.PENDING,
    )


@pytest.mark.asyncio
async def test_transition_pending_to_preparing():
    order_repo = AsyncMock(spec=OrderRepository)
    order_repo.get_by_id.return_value = _pending_order()

    order = await TransitionOrderStatus(order_repo).execute(42, OrderStatus.PREPARING)

    assert order.status == OrderStatus.PREPARING
    order_repo.update_status.assert_called_once_with(42, OrderStatus.PREPARING)


@pytest.mark.asyncio
async def test_transition_preparing_to_ready():
    order_repo = AsyncMock(spec=OrderRepository)
    order_repo.get_by_id.return_value = _pending_order()

    use_case = TransitionOrderStatus(order_repo)
    order = await use_case.execute(42, OrderStatus.PREPARING)
    assert order.status == OrderStatus.PREPARING

    order_repo.get_by_id.return_value = order
    order = await use_case.execute(42, OrderStatus.READY)
    assert order.status == OrderStatus.READY
    order_repo.update_status.assert_called_with(42, OrderStatus.READY)


@pytest.mark.asyncio
async def test_transition_ready_to_completed():
    order_repo = AsyncMock(spec=OrderRepository)
    order = _pending_order()
    order_repo.get_by_id.return_value = order
    use_case = TransitionOrderStatus(order_repo)

    for target in (OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.COMPLETED):
        order = await use_case.execute(42, target)
        order_repo.get_by_id.return_value = order

    assert order.status == OrderStatus.COMPLETED
    order_repo.update_status.assert_called_with(42, OrderStatus.COMPLETED)


@pytest.mark.asyncio
async def test_illegal_jump_pending_to_ready_raises():
    order_repo = AsyncMock(spec=OrderRepository)
    order_repo.get_by_id.return_value = _pending_order()

    with pytest.raises(ValueError, match="Cannot mark order ready"):
        await TransitionOrderStatus(order_repo).execute(42, OrderStatus.READY)
    order_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_transition_to_pending_raises():
    order_repo = AsyncMock(spec=OrderRepository)
    order_repo.get_by_id.return_value = _pending_order()

    with pytest.raises(ValueError, match="Cannot transition to PENDING"):
        await TransitionOrderStatus(order_repo).execute(42, OrderStatus.PENDING)
    order_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_transition_raises_when_order_missing():
    order_repo = AsyncMock(spec=OrderRepository)
    order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFound):
        await TransitionOrderStatus(order_repo).execute(999, OrderStatus.PREPARING)
    order_repo.update_status.assert_not_called()
