from decimal import Decimal

import pytest
from fakes import FakeUnitOfWork

from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound, ItemNotFound
from src.domain.item import Item
from src.usecases.add_cart_item import AddCartItem


async def test_add_item_to_cart_and_persist():
    uow = FakeUnitOfWork()
    cart = Cart(id=1, session_id="sess-1")
    uow.carts.get_by_session_id.return_value = cart
    item = Item(id=7, name="Burger", price=Decimal("9.99"), category="savory")
    uow.items.get_by_id.return_value = item

    use_case = AddCartItem(uow)
    result = await use_case.execute("sess-1", 7, 2)

    assert result.items[0].item_id == 7
    assert result.items[0].quantity == 2
    uow.carts.update.assert_called_once_with(cart)
    uow.items.get_by_id.assert_called_once_with(7)


async def test_add_item_merges_existing_quantity():
    uow = FakeUnitOfWork()
    cart = Cart(id=1, session_id="sess-1")
    uow.carts.get_by_session_id.return_value = cart
    item = Item(id=7, name="Burger", price=Decimal("9.99"), category="savory")
    uow.items.get_by_id.return_value = item

    use_case = AddCartItem(uow)
    await use_case.execute("sess-1", 7, 1)
    await use_case.execute("sess-1", 7, 2)

    assert cart.items[0].quantity == 3


async def test_add_item_raises_when_cart_missing():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = None

    use_case = AddCartItem(uow)
    with pytest.raises(CartNotFound):
        await use_case.execute("sess-ghost", 7, 1)


async def test_add_item_raises_when_item_missing():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = Cart(id=1, session_id="sess-1")
    uow.items.get_by_id.return_value = None

    use_case = AddCartItem(uow)
    with pytest.raises(ItemNotFound):
        await use_case.execute("sess-1", 999, 1)


async def test_add_item_rejects_non_positive_quantity():
    uow = FakeUnitOfWork()
    uow.carts.get_by_session_id.return_value = Cart(id=1, session_id="sess-1")
    uow.items.get_by_id.return_value = Item(
        id=7, name="Burger", price=Decimal("9.99"), category="savory"
    )

    use_case = AddCartItem(uow)
    with pytest.raises(ValueError, match="positive"):
        await use_case.execute("sess-1", 7, 0)
