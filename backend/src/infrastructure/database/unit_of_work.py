import asyncpg
from asyncpg.transaction import Transaction

from src.domain.repositories import UnitOfWork
from src.infrastructure.database.cart_repository import PostgresCartRepository
from src.infrastructure.database.coupon_repository import PostgresCouponRepository
from src.infrastructure.database.item_repository import PostgresItemRepository
from src.infrastructure.database.order_repository import PostgresOrderRepository
from src.infrastructure.database.payment_repository import PostgresPaymentRepository


class PostgresUnitOfWork(UnitOfWork):
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn
        self.carts = PostgresCartRepository(conn)
        self.items = PostgresItemRepository(conn)
        self.orders = PostgresOrderRepository(conn)
        self.payments = PostgresPaymentRepository(conn)
        self.coupons = PostgresCouponRepository(conn)
        self._tx: Transaction | None = None

    async def __aenter__(self) -> "PostgresUnitOfWork":
        self._tx = self._conn.transaction()
        await self._tx.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        tx = self._tx
        assert tx is not None
        if exc_type is None:
            await tx.commit()
        else:
            await tx.rollback()
