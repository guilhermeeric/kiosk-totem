import asyncpg

from src.domain.exceptions import ItemNotFound
from src.domain.item import Item
from src.domain.repositories import ItemRepository


class PostgresItemRepository(ItemRepository):
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def get_by_id(self, item_id: int) -> Item | None:
        row = await self._conn.fetchrow(
            "SELECT id, name, price, category, icon, stock FROM items WHERE id = $1",
            item_id,
        )
        if not row:
            return None
        return Item(
            id=row["id"],
            name=row["name"],
            price=row["price"],
            category=row["category"],
            icon=row["icon"],
            stock=row["stock"],
        )

    async def list_all(self) -> list[Item]:
        rows = await self._conn.fetch(
            "SELECT id, name, price, category, icon, stock FROM items ORDER BY category, name"
        )
        return [
            Item(
                id=row["id"],
                name=row["name"],
                price=row["price"],
                category=row["category"],
                icon=row["icon"],
                stock=row["stock"],
            )
            for row in rows
        ]

    async def consume_stock(self, item_id: int, quantity: int) -> None:
        # FOR UPDATE: within the checkout transaction this row-locks the item
        # so concurrent checkouts serialize — exactly one can consume the last
        # unit; the loser reads the decremented stock and fails the check.
        row = await self._conn.fetchrow(
            "SELECT id, name, stock FROM items WHERE id = $1 FOR UPDATE",
            item_id,
        )
        if row is None:
            raise ItemNotFound(f"Item {item_id} not found")
        if row["stock"] < quantity:
            raise ValueError(f"Only {row['stock']} left of {row['name']}")
        await self._conn.execute(
            "UPDATE items SET stock = stock - $2 WHERE id = $1",
            item_id,
            quantity,
        )

    async def add(self, item: Item) -> None:
        if item.id is not None:
            raise ValueError("Cannot add an item with an existing ID. Use update().")
        await self._conn.execute(
            "INSERT INTO items (name, price, category) VALUES ($1, $2, $3)",
            item.name,
            item.price,
            item.category,
        )

    async def update(self, item: Item) -> None:
        if item.id is None:
            raise ValueError("Cannot update an item without an ID. Use add().")
        result = await self._conn.execute(
            "UPDATE items SET name = $1, price = $2, category = $3 WHERE id = $4",
            item.name,
            item.price,
            item.category,
            item.id,
        )
        if result == "UPDATE 0":
            raise ValueError(f"Item with id {item.id} not found")
