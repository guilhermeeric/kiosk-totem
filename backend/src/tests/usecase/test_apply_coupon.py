from datetime import datetime
from decimal import Decimal

import pytest
from fakes import FakeUnitOfWork

from src.domain.cart import Cart, CartItem
from src.domain.coupon import Coupon
from src.domain.exceptions import CartNotFound, CouponNotFound
from src.usecases.apply_coupon import ApplyCoupon


def _coupon(code: str = "WELCOME10", quantity: int = 100) -> Coupon:
    return Coupon(
        coupon_code=code,
        total_discount=Decimal("10.00"),
        expiry_time=datetime(2099, 1, 1),
        quantity=quantity,
    )


async def test_apply_valid_coupon_snapshots_and_persists():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    cart.items = [CartItem(item_id=7, quantity=1, unit_price=Decimal("9.99"))]
    uow.carts.get_by_session_id.return_value = cart
    uow.coupons.get_by_code.return_value = _coupon()

    use_case = ApplyCoupon(uow)
    result = await use_case.execute("sess-1", "WELCOME10")

    assert result is cart
    assert result.coupon_code == "WELCOME10"
    assert result.coupon_discount == Decimal("10.00")
    uow.carts.update.assert_awaited_once_with(cart)


async def test_apply_unknown_code_raises_not_found_and_does_not_persist():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    uow.carts.get_by_session_id.return_value = cart
    uow.coupons.get_by_code.return_value = None

    with pytest.raises(CouponNotFound):
        await ApplyCoupon(uow).execute("sess-1", "NOPE99")

    uow.carts.update.assert_not_awaited()


async def test_apply_expired_coupon_raises_and_does_not_persist():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    uow.carts.get_by_session_id.return_value = cart
    uow.coupons.get_by_code.return_value = Coupon(
        coupon_code="OLD10",
        total_discount=Decimal("10.00"),
        expiry_time=datetime(2020, 1, 1),
        quantity=100,
    )

    with pytest.raises(ValueError, match="expired"):
        await ApplyCoupon(uow).execute("sess-1", "OLD10")

    uow.carts.update.assert_not_awaited()
    assert cart.coupon_code is None


async def test_apply_exhausted_coupon_raises_and_does_not_persist():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    uow.carts.get_by_session_id.return_value = cart
    uow.coupons.get_by_code.return_value = _coupon(code="GONE10", quantity=0)

    with pytest.raises(ValueError, match="no remaining uses"):
        await ApplyCoupon(uow).execute("sess-1", "GONE10")

    uow.carts.update.assert_not_awaited()
    assert cart.coupon_code is None


async def test_apply_missing_cart_raises_cart_not_found():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = None

    with pytest.raises(CartNotFound):
        await ApplyCoupon(uow).execute("sess-ghost", "WELCOME10")

    uow.coupons.get_by_code.assert_not_awaited()


async def test_apply_replaces_existing_coupon():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    cart.apply_coupon("OLDA", Decimal("5.00"))
    uow.carts.get_by_session_id.return_value = cart
    uow.coupons.get_by_code.return_value = _coupon(code="NEWB", quantity=50)

    result = await ApplyCoupon(uow).execute("sess-1", "NEWB")

    assert result.coupon_code == "NEWB"
    assert result.coupon_discount == Decimal("10.00")
    uow.carts.update.assert_awaited_once_with(cart)
