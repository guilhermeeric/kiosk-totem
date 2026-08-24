from unittest.mock import AsyncMock

from src.domain.repositories import (
    CartRepository,
    ItemRepository,
    OrderRepository,
    PaymentRepository,
    UnitOfWork,
)


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.carts = AsyncMock(spec=CartRepository)
        self.items = AsyncMock(spec=ItemRepository)
        self.orders = AsyncMock(spec=OrderRepository)
        self.payments = AsyncMock(spec=PaymentRepository)

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None
