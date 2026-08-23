from unittest.mock import AsyncMock

import pytest

from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound
from src.domain.repositories import CartRepository
from src.usecases.mark_cart_handed_off import MarkCartHandedOff


@pytest.mark.asyncio
async def test_mark_cart_handed_off_marks_existing_cart():
    cart_repo = AsyncMock(spec=CartRepository)
    cart_repo.get_by_session_id.return_value = Cart(id=7, session_id="sess-1")

    await MarkCartHandedOff(cart_repo).execute("sess-1")

    cart_repo.mark_handed_off.assert_called_once_with(7)


@pytest.mark.asyncio
async def test_mark_cart_handed_off_raises_when_cart_missing():
    cart_repo = AsyncMock(spec=CartRepository)
    cart_repo.get_by_session_id.return_value = None

    with pytest.raises(CartNotFound):
        await MarkCartHandedOff(cart_repo).execute("sess-ghost")
    cart_repo.mark_handed_off.assert_not_called()
