from decimal import Decimal

import pytest
from fakes import FakeUnitOfWork

from src.domain.cart import Cart, CartItem
from src.domain.exceptions import CartNotFound
from src.usecases.remove_cart_item import RemoveCartItem


async def test_remove_item_from_cart_and_persist():
    uow = FakeUnitOfWork()
    cart = Cart(id=1, session_id="sess-1")
    cart.items = [
        CartItem(item_id=7, quantity=1, unit_price=Decimal("9.99")),
        CartItem(item_id=8, quantity=2, unit_price=Decimal("3.50")),
    ]
    uow.carts.get_by_session_id.return_value = cart

    use_case = RemoveCartItem(uow)
    result = await use_case.execute("sess-1", 7)

    assert [ci.item_id for ci in result.items] == [8]
    uow.carts.update.assert_called_once_with(cart)


async def test_remove_item_not_in_cart_is_noop():
    uow = FakeUnitOfWork()
    cart = Cart(id=1, session_id="sess-1")
    uow.carts.get_by_session_id.return_value = cart

    use_case = RemoveCartItem(uow)
    result = await use_case.execute("sess-1", 999)

    assert result.items == []
    uow.carts.update.assert_called_once_with(cart)


async def test_remove_item_raises_when_cart_missing():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = None

    use_case = RemoveCartItem(uow)
    with pytest.raises(CartNotFound):
        await use_case.execute("sess-ghost", 7)
