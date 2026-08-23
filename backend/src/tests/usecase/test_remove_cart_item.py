from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.cart import Cart, CartItem
from src.domain.exceptions import CartNotFound
from src.domain.repositories import CartRepository
from src.usecases.remove_cart_item import RemoveCartItem


@pytest.mark.asyncio
async def test_remove_item_from_cart_and_persist():
    cart_repo = AsyncMock(spec=CartRepository)
    cart = Cart(id=1, session_id="sess-1")
    cart.items = [
        CartItem(item_id=7, quantity=1, unit_price=Decimal("9.99")),
        CartItem(item_id=8, quantity=2, unit_price=Decimal("3.50")),
    ]
    cart_repo.get_by_session_id.return_value = cart

    use_case = RemoveCartItem(cart_repo)
    result = await use_case.execute("sess-1", 7)

    assert [ci.item_id for ci in result.items] == [8]
    cart_repo.update.assert_called_once_with(cart)


@pytest.mark.asyncio
async def test_remove_item_not_in_cart_is_noop():
    cart_repo = AsyncMock(spec=CartRepository)
    cart = Cart(id=1, session_id="sess-1")
    cart_repo.get_by_session_id.return_value = cart

    use_case = RemoveCartItem(cart_repo)
    result = await use_case.execute("sess-1", 999)

    assert result.items == []
    cart_repo.update.assert_called_once_with(cart)


@pytest.mark.asyncio
async def test_remove_item_raises_when_cart_missing():
    cart_repo = AsyncMock(spec=CartRepository)
    cart_repo.get_by_session_id.return_value = None

    use_case = RemoveCartItem(cart_repo)
    with pytest.raises(CartNotFound):
        await use_case.execute("sess-ghost", 7)
