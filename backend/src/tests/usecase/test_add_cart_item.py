from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound, ItemNotFound
from src.domain.item import Item
from src.domain.repositories import CartRepository, ItemRepository
from src.usecases.add_cart_item import AddCartItem


@pytest.mark.asyncio
async def test_add_item_to_cart_and_persist():
    cart_repo = AsyncMock(spec=CartRepository)
    item_repo = AsyncMock(spec=ItemRepository)
    cart = Cart(id=1, session_id="sess-1")
    cart_repo.get_by_session_id.return_value = cart
    item = Item(id=7, name="Burger", price=Decimal("9.99"), category="savory")
    item_repo.get_by_id.return_value = item

    use_case = AddCartItem(cart_repo, item_repo)
    result = await use_case.execute("sess-1", 7, 2)

    assert result.items[0].item_id == 7
    assert result.items[0].quantity == 2
    cart_repo.update.assert_called_once_with(cart)
    item_repo.get_by_id.assert_called_once_with(7)


@pytest.mark.asyncio
async def test_add_item_merges_existing_quantity():
    cart_repo = AsyncMock(spec=CartRepository)
    item_repo = AsyncMock(spec=ItemRepository)
    cart = Cart(id=1, session_id="sess-1")
    cart_repo.get_by_session_id.return_value = cart
    item = Item(id=7, name="Burger", price=Decimal("9.99"), category="savory")
    item_repo.get_by_id.return_value = item

    use_case = AddCartItem(cart_repo, item_repo)
    await use_case.execute("sess-1", 7, 1)
    await use_case.execute("sess-1", 7, 2)

    assert cart.items[0].quantity == 3


@pytest.mark.asyncio
async def test_add_item_raises_when_cart_missing():
    cart_repo = AsyncMock(spec=CartRepository)
    item_repo = AsyncMock(spec=ItemRepository)
    cart_repo.get_by_session_id.return_value = None

    use_case = AddCartItem(cart_repo, item_repo)
    with pytest.raises(CartNotFound):
        await use_case.execute("sess-ghost", 7, 1)


@pytest.mark.asyncio
async def test_add_item_raises_when_item_missing():
    cart_repo = AsyncMock(spec=CartRepository)
    item_repo = AsyncMock(spec=ItemRepository)
    cart_repo.get_by_session_id.return_value = Cart(id=1, session_id="sess-1")
    item_repo.get_by_id.return_value = None

    use_case = AddCartItem(cart_repo, item_repo)
    with pytest.raises(ItemNotFound):
        await use_case.execute("sess-1", 999, 1)


@pytest.mark.asyncio
async def test_add_item_rejects_non_positive_quantity():
    cart_repo = AsyncMock(spec=CartRepository)
    item_repo = AsyncMock(spec=ItemRepository)
    cart_repo.get_by_session_id.return_value = Cart(id=1, session_id="sess-1")
    item_repo.get_by_id.return_value = Item(
        id=7, name="Burger", price=Decimal("9.99"), category="savory"
    )

    use_case = AddCartItem(cart_repo, item_repo)
    with pytest.raises(ValueError, match="positive"):
        await use_case.execute("sess-1", 7, 0)
