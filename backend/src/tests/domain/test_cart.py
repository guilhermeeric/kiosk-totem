from decimal import Decimal

import pytest

from src.domain.cart import Cart
from src.domain.item import Item


def test_cart_add_new_item():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, quantity=2)
    assert len(cart.items) == 1
    assert cart.items[0].item_id == 1
    assert cart.items[0].quantity == 2
    assert cart.items[0].unit_price == Decimal("9.99")
    assert cart.total() == Decimal("19.98")


def test_cart_add_existing_item_merges():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, 2)
    cart.add_item(item, 3)
    assert len(cart.items) == 1
    assert cart.items[0].quantity == 5
    assert cart.total() == Decimal("49.95")


def test_cart_remove_item():
    cart = Cart(id=1, session_id="sess-1")
    item1 = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    item2 = Item(id=2, name="Fries", price=Decimal("3.50"), category="savory")
    cart.add_item(item1, 1)
    cart.add_item(item2, 1)
    cart.remove_item(1)
    assert len(cart.items) == 1
    assert cart.items[0].item_id == 2
    assert cart.total() == Decimal("3.50")


def test_cart_update_quantity():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, 2)
    cart.update_quantity(1, 5)
    assert cart.items[0].quantity == 5
    assert cart.total() == Decimal("49.95")


def test_cart_update_quantity_to_zero_removes():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, 2)
    cart.update_quantity(1, 0)
    assert len(cart.items) == 0
    assert cart.total() == Decimal("0")


def test_cart_is_empty():
    cart = Cart(id=1, session_id="sess-1")
    assert cart.is_empty() is True
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, 1)
    assert cart.is_empty() is False


def test_cart_add_negative_quantity_raises():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    with pytest.raises(ValueError, match="Quantity must be positive"):
        cart.add_item(item, -1)


def test_cart_add_quantity_over_cap_raises():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    with pytest.raises(ValueError, match="99"):
        cart.add_item(item, 100)


def test_cart_update_quantity_over_cap_raises():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, 1)
    with pytest.raises(ValueError, match="99"):
        cart.update_quantity(1, 100)


def test_cart_update_negative_quantity_raises():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, 1)
    with pytest.raises(ValueError, match="Quantity cannot be negative"):
        cart.update_quantity(1, -1)


def test_cart_update_nonexistent_item_raises():
    cart = Cart(id=1, session_id="sess-1")
    with pytest.raises(ValueError, match="Item 999 not in cart"):
        cart.update_quantity(999, 1)


def test_cart_item_count():
    cart = Cart(id=1, session_id="sess-1")
    item1 = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    item2 = Item(id=2, name="Fries", price=Decimal("3.50"), category="savory")
    cart.add_item(item1, 2)
    cart.add_item(item2, 3)
    assert cart.item_count() == 5


def test_cart_apply_coupon_attaches_snapshot():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, 2)
    cart.apply_coupon("WELCOME10", 10)
    assert cart.coupon_code == "WELCOME10"
    assert cart.coupon_percent == 10  # snapshot is the percent, not money
    assert cart.subtotal() == Decimal("19.98")
    # 10% of 19.98 = 1.998, rounded half-up to cents
    assert cart.discount() == Decimal("2.00")
    assert cart.total() == Decimal("17.98")


def test_cart_ten_percent_discount_rounds_half_up():
    cart = Cart(id=1, session_id="sess-1")
    cart.add_item(Item(id=1, name="Burger", price=Decimal("9.99"), category="savory"), 1)
    cart.add_item(Item(id=2, name="Fries", price=Decimal("3.50"), category="savory"), 1)
    cart.apply_coupon("WELCOME10", 10)
    assert cart.subtotal() == Decimal("13.49")
    assert cart.discount() == Decimal("1.35")  # 1.349 rounds half-up
    assert cart.total() == Decimal("12.14")


def test_cart_full_percent_coupon_never_exceeds_subtotal():
    cart = Cart(id=1, session_id="sess-1")
    cart.add_item(Item(id=1, name="Coffee", price=Decimal("2.50"), category="beverages"), 1)
    cart.apply_coupon("FREE", 100)
    assert cart.coupon_percent == 100  # snapshot kept verbatim
    assert cart.discount() == Decimal("2.50")
    assert cart.total() == Decimal("0.00")
    assert cart.subtotal() == Decimal("2.50")


def test_cart_discount_scales_with_subtotal():
    # percent snapshot stays 10; the money discount follows the live subtotal
    cart = Cart(id=1, session_id="sess-1")
    cart.add_item(Item(id=1, name="Coffee", price=Decimal("2.50"), category="beverages"), 1)
    cart.apply_coupon("WELCOME10", 10)
    assert cart.discount() == Decimal("0.25")
    assert cart.total() == Decimal("2.25")
    cart.add_item(Item(id=2, name="Burger", price=Decimal("9.99"), category="savory"), 1)
    assert cart.subtotal() == Decimal("12.49")
    assert cart.discount() == Decimal("1.25")  # 1.249 rounds half-up
    assert cart.total() == Decimal("11.24")


def test_cart_apply_coupon_replaces_existing():
    cart = Cart(id=1, session_id="sess-1")
    cart.apply_coupon("OLDA", 5)
    cart.apply_coupon("NEWB", 50)
    assert cart.coupon_code == "NEWB"
    assert cart.coupon_percent == 50


def test_cart_remove_coupon_clears():
    cart = Cart(id=1, session_id="sess-1")
    cart.add_item(Item(id=1, name="Coffee", price=Decimal("2.50"), category="beverages"), 1)
    cart.apply_coupon("WELCOME10", 10)
    cart.remove_coupon()
    assert cart.coupon_code is None
    assert cart.coupon_percent == 0
    assert cart.discount() == Decimal("0.00")
    assert cart.total() == cart.subtotal() == Decimal("2.50")


def test_cart_total_without_coupon_unchanged():
    cart = Cart(id=1, session_id="sess-1")
    item = Item(id=1, name="Burger", price=Decimal("9.99"), category="savory")
    cart.add_item(item, 2)
    assert cart.total() == cart.subtotal() == Decimal("19.98")
