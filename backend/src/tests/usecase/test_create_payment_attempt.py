from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.exceptions import OrderNotFound
from src.domain.order import Order, OrderStatus, OrderType
from src.domain.payment import Payment, PaymentMethod, PaymentStatus
from src.domain.repositories import OrderRepository, PaymentRepository
from src.usecases.create_payment_attempt import CreatePaymentAttempt


async def test_create_payment_attempt_pays_order():
    order_repo = AsyncMock(spec=OrderRepository)
    payment_repo = AsyncMock(spec=PaymentRepository)
    order_repo.get_by_id.return_value = Order(
        id=42,
        cart_id=3,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("23.48"),
        status=OrderStatus.PENDING,
    )

    async def fake_create(payment: Payment) -> None:
        payment.id = 100

    payment_repo.create.side_effect = fake_create

    use_case = CreatePaymentAttempt(order_repo, payment_repo)
    payment = await use_case.execute(42, PaymentMethod.PIX)

    assert payment.id == 100
    assert payment.order_id == 42
    assert payment.method == PaymentMethod.PIX
    assert payment.status == PaymentStatus.PAID
    payment_repo.create.assert_called_once()


async def test_create_payment_attempt_raises_when_order_missing():
    order_repo = AsyncMock(spec=OrderRepository)
    payment_repo = AsyncMock(spec=PaymentRepository)
    order_repo.get_by_id.return_value = None

    use_case = CreatePaymentAttempt(order_repo, payment_repo)
    with pytest.raises(OrderNotFound, match="42"):
        await use_case.execute(42, PaymentMethod.CASH)
    payment_repo.create.assert_not_called()


async def test_create_payment_attempt_declines_non_paid_outcome():
    """Simulated decline: any outcome other than PAID rejects the payment
    without persisting anything. The checkout transaction rolls back, so no
    order ever exists unpaid."""
    order_repo = AsyncMock(spec=OrderRepository)
    payment_repo = AsyncMock(spec=PaymentRepository)
    order_repo.get_by_id.return_value = Order(
        id=42,
        cart_id=3,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("23.48"),
        status=OrderStatus.PENDING,
    )

    use_case = CreatePaymentAttempt(order_repo, payment_repo)
    with pytest.raises(ValueError, match="Payment declined"):
        await use_case.execute(42, PaymentMethod.CREDIT_CARD, PaymentStatus.FAILED)
    payment_repo.create.assert_not_called()
