from unittest.mock import AsyncMock

import pytest

from src.domain.cart import Cart
from src.domain.exceptions import CartNotFound
from src.domain.repositories import CartRepository
from src.usecases.get_cart import GetCart


@pytest.mark.asyncio
async def test_get_cart_returns_existing_cart():
    mock_repo = AsyncMock(spec=CartRepository)
    expected = Cart(id=1, session_id="sess-1")
    mock_repo.get_by_session_id.return_value = expected

    use_case = GetCart(mock_repo)
    cart = await use_case.execute("sess-1")

    assert cart is expected
    mock_repo.get_by_session_id.assert_called_once_with("sess-1")


@pytest.mark.asyncio
async def test_get_cart_raises_when_not_found():
    mock_repo = AsyncMock(spec=CartRepository)
    mock_repo.get_by_session_id.return_value = None

    use_case = GetCart(mock_repo)
    with pytest.raises(CartNotFound, match="sess-missing"):
        await use_case.execute("sess-missing")
