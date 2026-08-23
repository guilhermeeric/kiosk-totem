from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.cart import Cart, CartItem
from src.domain.exceptions import CartNotFound
from src.domain.order import Order, OrderStatus, OrderType
from src.domain.payment import PaymentMethod, PaymentStatus
from src.domain.repositories import CartRepository, OrderRepository, PaymentRepository
from src.usecases.checkout import Checkout


@pytest.mark.asyncio
async def test_checkout_creates_order_with_payment_attempt():
    cart_repo = AsyncMock(spec=CartRepository)
    order_repo = AsyncMock(spec=OrderRepository)
    payment_repo = AsyncMock(spec=PaymentRepository)
    cart = Cart(id=3, session_id="sess-1")
    cart.items = [
        CartItem(item_id=7, quantity=2, unit_price=Decimal("9.99")),
        CartItem(item_id=8, quantity=1, unit_price=Decimal("3.50")),
    ]
    cart_repo.get_by_session_id.return_value = cart

    async def fake_create(order: Order) -> None:
        order.id = 42

    order_repo.create.side_effect = fake_create
    # CreatePaymentAttempt re-fetches the order it validates before paying.
    order_repo.get_by_id.return_value = Order(
        id=42,
        cart_id=3,
        customer_name="Alice",
        order_type=OrderType.EAT_IN,
        items=[],
        total=Decimal("0"),
    )

    async def fake_payment_create(payment) -> None:
        payment.id = 100

    payment_repo.create.side_effect = fake_payment_create

    use_case = Checkout(cart_repo, order_repo, payment_repo)
    order = await use_case.execute(
        "sess-1",
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        payment_method=PaymentMethod.PIX,
    )

    assert order.id == 42
    assert order.cart_id == 3
    assert order.customer_name == "Alice"
    assert order.order_type == OrderType.TAKEAWAY
    assert order.status == OrderStatus.PENDING
    assert order.total == Decimal("23.48")
    assert [oi.item_id for oi in order.items] == [7, 8]
    assert order.items[0].quantity == 2
    # The order is created already paid: exactly one PAID payment attached.
    assert len(order.payments) == 1
    assert order.payments[0].id == 100
    assert order.payments[0].order_id == 42
    assert order.payments[0].method == PaymentMethod.PIX
    assert order.payments[0].status == PaymentStatus.PAID
    payment_repo.create.assert_called_once()
    # Cart is left untouched: one-order-per-cart is enforced by the DB.
    assert [ci.item_id for ci in cart.items] == [7, 8]
    cart_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_checkout_rejects_empty_cart():
    cart_repo = AsyncMock(spec=CartRepository)
    order_repo = AsyncMock(spec=OrderRepository)
    payment_repo = AsyncMock(spec=PaymentRepository)
    cart_repo.get_by_session_id.return_value = Cart(id=3, session_id="sess-1")

    use_case = Checkout(cart_repo, order_repo, payment_repo)
    with pytest.raises(ValueError, match="empty"):
        await use_case.execute(
            "sess-1",
            customer_name="Alice",
            order_type=OrderType.EAT_IN,
            payment_method=PaymentMethod.CASH,
        )
    order_repo.create.assert_not_called()
    payment_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_checkout_raises_when_cart_missing():
    cart_repo = AsyncMock(spec=CartRepository)
    order_repo = AsyncMock(spec=OrderRepository)
    payment_repo = AsyncMock(spec=PaymentRepository)
    cart_repo.get_by_session_id.return_value = None

    use_case = Checkout(cart_repo, order_repo, payment_repo)
    with pytest.raises(CartNotFound):
        await use_case.execute(
            "sess-ghost",
            customer_name="Alice",
            order_type=OrderType.EAT_IN,
            payment_method=PaymentMethod.DEBIT_CARD,
        )
    order_repo.create.assert_not_called()
    payment_repo.create.assert_not_called()
