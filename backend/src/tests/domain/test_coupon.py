from datetime import datetime
from decimal import Decimal

import pytest

from src.domain.cart import Cart
from src.domain.coupon import Coupon
from src.domain.item import Item


def test_coupon_add_attaches_snapshot_when_active():
    cart = Cart(session_id="sess-1")
    coupon = Coupon(
        coupon_code="WELCOME10",
        total_discount=Decimal("10.00"),
        expiry_time=datetime(2026, 10, 1, 12, 0),
        quantity=100,
    )
    coupon.add(cart, now=datetime(2026, 9, 30, 12, 0))
    assert cart.coupon_code == "WELCOME10"
    assert cart.coupon_discount == Decimal("10.00")


def test_coupon_add_refuses_at_expiry_instant_and_leaves_cart_unchanged():
    cart = Cart(session_id="sess-1")
    coupon = Coupon(
        coupon_code="WELCOME10",
        total_discount=Decimal("10.00"),
        expiry_time=datetime(2026, 10, 1, 12, 0),
        quantity=100,
    )
    with pytest.raises(ValueError, match="expired"):
        coupon.add(cart, now=datetime(2026, 10, 1, 12, 0))  # now == expiry_time is expired
    assert cart.coupon_code is None
    assert cart.coupon_discount == Decimal("0")


def test_coupon_add_refuses_when_no_uses_left_and_leaves_cart_unchanged():
    cart = Cart(session_id="sess-1")
    coupon = Coupon(
        coupon_code="GONE10",
        total_discount=Decimal("10.00"),
        expiry_time=datetime(2099, 1, 1),
        quantity=0,
    )
    with pytest.raises(ValueError, match="no remaining uses"):
        coupon.add(cart, now=datetime(2026, 9, 30, 12, 0))
    assert cart.coupon_code is None
    assert cart.coupon_discount == Decimal("0")


def test_coupon_add_snapshots_full_value_regardless_of_subtotal():
    # Proportional clamp is Cart.discount()'s job; the snapshot stays verbatim.
    cart = Cart(session_id="sess-1")
    cart.add_item(Item(id=1, name="Coffee", price=Decimal("2.50"), category="beverages"), 1)
    coupon = Coupon(
        coupon_code="BIG10",
        total_discount=Decimal("10.00"),
        expiry_time=datetime(2099, 1, 1),
        quantity=100,
    )
    coupon.add(cart, now=datetime(2026, 9, 30, 12, 0))
    assert cart.coupon_discount == Decimal("10.00")  # snapshot verbatim
    assert cart.total() == Decimal("0.00")  # clamped when computing
