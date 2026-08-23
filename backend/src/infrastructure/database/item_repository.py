import asyncpg

from src.domain.item import Item
from src.domain.repositories import ItemRepository


class PostgresItemRepository(ItemRepository):
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def get_by_id(self, item_id: int) -> Item | None:
        row = await self._conn.fetchrow(
            "SELECT id, name, price, category FROM items WHERE id = $1",
            item_id,
        )
        if not row:
            return None
        return Item(
            id=row["id"],
            name=row["name"],
            price=row["price"],
            category=row["category"],
        )

    async def list_all(self) -> list[Item]:
        rows = await self._conn.fetch(
            "SELECT id, name, price, category FROM items ORDER BY category, name"
        )
        return [
            Item(
                id=row["id"],
                name=row["name"],
                price=row["price"],
                category=row["category"],
            )
            for row in rows
        ]

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
