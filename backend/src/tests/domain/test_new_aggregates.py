from decimal import Decimal

from src.domain.cart import Cart
from src.domain.item import Item
from src.domain.order import Order, OrderType


def test_new_cart_has_no_id():
    cart = Cart(session_id="sess-1")
    assert cart.id is None
    assert cart.items == []


def test_new_item_has_no_id():
    item = Item(name="Burger", price=Decimal("9.99"), category="savory")
    assert item.id is None


def test_new_order_has_no_id():
    order = Order(
        cart_id=1,
        customer_name="Alice",
        order_type=OrderType.TAKEAWAY,
        items=[],
        total=Decimal("0"),
    )
    assert order.id is None
    assert order.status.value == "PENDING"
