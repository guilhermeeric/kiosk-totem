from decimal import Decimal

import pytest
from fakes import FakeUnitOfWork

from src.domain.cart import Cart, CartItem
from src.domain.exceptions import CartNotFound
from src.domain.order import Order, OrderStatus, OrderType
from src.domain.payment import PaymentMethod, PaymentStatus
from src.usecases.checkout import Checkout


@pytest.mark.asyncio
async def test_checkout_creates_order_with_payment_attempt():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    # Items deliberately out of order: stock must be consumed sorted by item_id
    # so concurrent checkouts lock rows in a consistent order (no deadlock).
    cart.items = [
        CartItem(item_id=8, quantity=1, unit_price=Decimal("3.50")),
        CartItem(item_id=7, quantity=2, unit_price=Decimal("9.99")),
    ]
    uow.carts.get_by_session_id.return_value = cart

    async def fake_create(order: Order) -> None:
        order.id = 42

    uow.orders.create.side_effect = fake_create
    # CreatePaymentAttempt re-fetches the order it validates before paying.
    uow.orders.get_by_id.return_value = Order(
        id=42,
        cart_id=3,
        customer_name="Alice",
        order_type=OrderType.EAT_IN,
        items=[],
        total=Decimal("0"),
    )

    async def fake_payment_create(payment) -> None:
        payment.id = 100

    uow.payments.create.side_effect = fake_payment_create

    use_case = Checkout(uow)
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
    assert [oi.item_id for oi in order.items] == [8, 7]
    # Stock consumed per line, in item_id order, before the order is written.
    assert uow.items.consume_stock.call_count == 2
    assert uow.items.consume_stock.call_args_list[0].args == (7, 2)
    assert uow.items.consume_stock.call_args_list[1].args == (8, 1)
    # The order is created already paid: exactly one PAID payment attached.
    assert len(order.payments) == 1
    assert order.payments[0].id == 100
    assert order.payments[0].order_id == 42
    assert order.payments[0].method == PaymentMethod.PIX
    assert order.payments[0].status == PaymentStatus.PAID
    uow.payments.create.assert_called_once()
    # Cart is left untouched: one-order-per-cart is enforced by the DB.
    assert [ci.item_id for ci in cart.items] == [8, 7]
    uow.carts.update.assert_not_called()


@pytest.mark.asyncio
async def test_checkout_aborts_when_stock_insufficient():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    cart.items = [CartItem(item_id=7, quantity=2, unit_price=Decimal("9.99"))]
    uow.carts.get_by_session_id.return_value = cart
    uow.items.consume_stock.side_effect = ValueError("Only 1 left of Coffee")

    use_case = Checkout(uow)
    with pytest.raises(ValueError, match="Only 1 left"):
        await use_case.execute(
            "sess-1",
            customer_name="Alice",
            order_type=OrderType.EAT_IN,
            payment_method=PaymentMethod.PIX,
        )
    # Nothing may be persisted when stock is insufficient.
    uow.orders.create.assert_not_called()
    uow.payments.create.assert_not_called()


@pytest.mark.asyncio
async def test_checkout_rejects_empty_cart():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = Cart(id=3, session_id="sess-1")

    use_case = Checkout(uow)
    with pytest.raises(ValueError, match="empty"):
        await use_case.execute(
            "sess-1",
            customer_name="Alice",
            order_type=OrderType.EAT_IN,
            payment_method=PaymentMethod.CASH,
        )
    uow.orders.create.assert_not_called()
    uow.payments.create.assert_not_called()
    uow.items.consume_stock.assert_not_called()


@pytest.mark.asyncio
async def test_checkout_raises_when_cart_missing():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = None

    use_case = Checkout(uow)
    with pytest.raises(CartNotFound):
        await use_case.execute(
            "sess-ghost",
            customer_name="Alice",
            order_type=OrderType.EAT_IN,
            payment_method=PaymentMethod.DEBIT_CARD,
        )
    uow.orders.create.assert_not_called()
    uow.payments.create.assert_not_called()


@pytest.mark.asyncio
async def test_checkout_declines_failed_payment_outcome():
    """Simulated decline at checkout: the payment rejects and the unit of
    work rolls back, so the order and stock consumption never commit — an
    unpaid order cannot exist."""
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    cart.items = [CartItem(item_id=7, quantity=1, unit_price=Decimal("9.99"))]
    uow.carts.get_by_session_id.return_value = cart

    async def fake_create(order: Order) -> None:
        order.id = 42

    uow.orders.create.side_effect = fake_create

    use_case = Checkout(uow)
    with pytest.raises(ValueError, match="Payment declined"):
        await use_case.execute(
            "sess-1",
            customer_name="Alice",
            order_type=OrderType.EAT_IN,
            payment_method=PaymentMethod.PIX,
            payment_status=PaymentStatus.FAILED,
        )
    uow.payments.create.assert_not_called()
