from decimal import Decimal

import pytest
from fakes import FakeUnitOfWork

from src.domain.cart import Cart, CartItem
from src.domain.exceptions import CartNotFound
from src.usecases.update_cart_item import UpdateCartItem


@pytest.mark.asyncio
async def test_update_quantity_and_persist():
    uow = FakeUnitOfWork()
    cart = Cart(id=1, session_id="sess-1")
    cart.items = [CartItem(item_id=7, quantity=1, unit_price=Decimal("9.99"))]
    uow.carts.get_by_session_id.return_value = cart

    use_case = UpdateCartItem(uow)
    result = await use_case.execute("sess-1", 7, 5)

    assert result.items[0].quantity == 5
    uow.carts.update.assert_called_once_with(cart)


@pytest.mark.asyncio
async def test_update_quantity_to_zero_removes_item():
    uow = FakeUnitOfWork()
    cart = Cart(id=1, session_id="sess-1")
    cart.items = [CartItem(item_id=7, quantity=1, unit_price=Decimal("9.99"))]
    uow.carts.get_by_session_id.return_value = cart

    use_case = UpdateCartItem(uow)
    result = await use_case.execute("sess-1", 7, 0)

    assert result.items == []


@pytest.mark.asyncio
async def test_update_quantity_rejects_negative():
    uow = FakeUnitOfWork()
    cart = Cart(id=1, session_id="sess-1")
    cart.items = [CartItem(item_id=7, quantity=1, unit_price=Decimal("9.99"))]
    uow.carts.get_by_session_id.return_value = cart

    use_case = UpdateCartItem(uow)
    with pytest.raises(ValueError, match="negative"):
        await use_case.execute("sess-1", 7, -1)


@pytest.mark.asyncio
async def test_update_quantity_rejects_item_not_in_cart():
    uow = FakeUnitOfWork()
    cart = Cart(id=1, session_id="sess-1")
    uow.carts.get_by_session_id.return_value = cart

    use_case = UpdateCartItem(uow)
    with pytest.raises(ValueError, match="not in cart"):
        await use_case.execute("sess-1", 999, 2)


@pytest.mark.asyncio
async def test_update_quantity_raises_when_cart_missing():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = None

    use_case = UpdateCartItem(uow)
    with pytest.raises(CartNotFound):
        await use_case.execute("sess-ghost", 7, 2)
