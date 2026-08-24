import pytest
from fakes import FakeUnitOfWork

from src.domain.cart import Cart
from src.usecases.create_cart import CreateCart


@pytest.mark.asyncio
async def test_create_cart_returns_cart_with_assigned_id():
    uow = FakeUnitOfWork()

    async def fake_create(cart: Cart) -> None:
        cart.id = 42

    uow.carts.create.side_effect = fake_create

    use_case = CreateCart(uow)
    cart = await use_case.execute("sess-1")

    assert cart.session_id == "sess-1"
    assert cart.id == 42
    assert cart.items == []
    uow.carts.create.assert_called_once()
