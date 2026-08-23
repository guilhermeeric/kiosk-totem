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
