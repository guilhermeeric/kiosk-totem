from decimal import Decimal

import pytest
from fakes import FakeUnitOfWork

from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound
from src.usecases.remove_coupon import RemoveCoupon


async def test_remove_coupon_clears_and_persists():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    cart.apply_coupon("WELCOME10", Decimal("10.00"))
    uow.carts.get_by_session_id.return_value = cart

    result = await RemoveCoupon(uow).execute("sess-1")

    assert result is cart
    assert result.coupon_code is None
    assert result.coupon_discount == Decimal("0")
    uow.carts.update.assert_awaited_once_with(cart)


async def test_remove_coupon_without_coupon_is_a_noop():
    uow = FakeUnitOfWork()
    cart = Cart(id=3, session_id="sess-1")
    uow.carts.get_by_session_id.return_value = cart

    result = await RemoveCoupon(uow).execute("sess-1")

    assert result.coupon_code is None
    uow.carts.update.assert_awaited_once_with(cart)


async def test_remove_coupon_missing_cart_raises():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = None

    with pytest.raises(CartNotFound):
        await RemoveCoupon(uow).execute("sess-ghost")

    uow.carts.update.assert_not_awaited()
