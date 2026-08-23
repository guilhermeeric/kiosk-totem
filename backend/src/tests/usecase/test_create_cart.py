from unittest.mock import AsyncMock

import pytest

from src.domain.cart import Cart
from src.domain.repositories import CartRepository
from src.usecases.create_cart import CreateCart


@pytest.mark.asyncio
async def test_create_cart_returns_cart_with_assigned_id():
    mock_repo = AsyncMock(spec=CartRepository)

    async def fake_create(cart: Cart) -> None:
        cart.id = 42

    mock_repo.create.side_effect = fake_create

    use_case = CreateCart(mock_repo)
    cart = await use_case.execute("sess-1")

    assert cart.session_id == "sess-1"
    assert cart.id == 42
    assert cart.items == []
    mock_repo.create.assert_called_once()
