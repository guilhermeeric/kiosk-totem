from decimal import Decimal
import pytest
from datetime import datetime
from src.domain.order import (
    Order,
    OrderItem,
    OrderType,
    OrderStatus,
    PaymentStatus,
)

def test_order_creation():
    order = Order(
        id=1,
        cart_id=1,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[
            OrderItem(item_id=1, quantity=2, unit_price=Decimal("9.99")),
        ],
        total=Decimal("19.98"),
    )
    assert order.id == 1
    assert order.cart_id == 1
    assert order.customer_name == "Alice"
    assert order.order_type == OrderType.TAKEAWAY
    assert order.status == OrderStatus.PENDING
    assert order.payment_status == PaymentStatus.PENDING
    assert order.total == Decimal("19.98")

def test_order_status_transitions():
    order = Order(
        id=1,
        cart_id=1,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("0"),
    )
    order.mark_preparing()
    assert order.status == OrderStatus.PREPARING

    order.mark_ready()
    assert order.status == OrderStatus.READY

    order.mark_completed()
    assert order.status == OrderStatus.COMPLETED

def test_order_cancel_before_completed():
    order = Order(
        id=1,
        cart_id=1,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("0"),
        status=OrderStatus.PENDING,
    )
    order.cancel()
    assert order.status == OrderStatus.CANCELLED

def test_order_cancel_after_completed_raises():
    order = Order(
        id=1,
        cart_id=1,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("0"),
        status=OrderStatus.COMPLETED,
    )
    with pytest.raises(ValueError, match="Cannot cancel a completed order"):
        order.cancel()

def test_order_payment_transitions():
    order = Order(
        id=1,
        cart_id=1,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("0"),
    )
    order.mark_paid()
    assert order.payment_status == PaymentStatus.PAID

    # Reset for failed test
    order = Order(
        id=1,
        cart_id=1,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("0"),
    )
    order.mark_payment_failed()
    assert order.payment_status == PaymentStatus.FAILED

def test_order_item_total():
    item = OrderItem(item_id=1, quantity=2, unit_price=Decimal("9.99"))
    assert item.total() == Decimal("19.98")
