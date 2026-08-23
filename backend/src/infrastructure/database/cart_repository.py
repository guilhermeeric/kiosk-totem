import asyncpg

from src.domain.cart import Cart, CartItem
from src.domain.repositories import CartRepository


class PostgresCartRepository(CartRepository):
    """PostgreSQL implementation of the CartRepository interface."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def get_by_session_id(self, session_id: str) -> Cart | None:
        # FOR UPDATE: within a transaction (cart mutations) this row-locks the
        # cart so concurrent read-modify-write flows serialize instead of
        # losing updates. Harmless in autocommit (read endpoints).
        row = await self._conn.fetchrow(
            "SELECT id, session_id FROM carts WHERE session_id = $1 FOR UPDATE",
            session_id,
        )
        if not row:
            return None

        cart = Cart(id=row["id"], session_id=row["session_id"])
        cart.items = await self._load_items(cart.id)
        return cart

    async def create(self, cart: Cart) -> None:
        """
        Insert a new cart and its items.
        Cart.id must be None; the database will assign a BIGSERIAL.
        """
        if cart.id is not None:
            raise ValueError("Cannot create a cart with an existing ID. Use update() instead.")
        try:
            cart_id = await self._conn.fetchval(
                "INSERT INTO carts (session_id) VALUES ($1) RETURNING id",
                cart.session_id,
            )
        except asyncpg.UniqueViolationError:
            # carts.session_id is unique: one cart per session.
            raise ValueError("A session can only have one cart") from None
        cart.id = cart_id  # Update the domain object with the assigned ID

        # Insert items
        if cart.items:
            values = [(cart_id, ci.item_id, ci.quantity, ci.unit_price) for ci in cart.items]
            await self._conn.executemany(
                """
                INSERT INTO cart_items (cart_id, item_id, quantity, unit_price)
                VALUES ($1, $2, $3, $4)
                """,
                values,
            )

    async def update(self, cart: Cart) -> None:
        """
        Update an existing cart and replace all its items.
        Cart.id must not be None.
        """
        if cart.id is None:
            raise ValueError("Cannot update a cart without an ID. Use create() instead.")
        # Update cart session_id (though it rarely changes)
        result = await self._conn.execute(
            "UPDATE carts SET session_id = $1 WHERE id = $2",
            cart.session_id,
            cart.id,
        )
        if result == "UPDATE 0":
            raise ValueError(f"Cart with id {cart.id} not found")
        # Replace items (delete old, insert new)
        await self._conn.execute(
            "DELETE FROM cart_items WHERE cart_id = $1",
            cart.id,
        )
        if cart.items:
            values = [(cart.id, ci.item_id, ci.quantity, ci.unit_price) for ci in cart.items]
            await self._conn.executemany(
                """
                INSERT INTO cart_items (cart_id, item_id, quantity, unit_price)
                VALUES ($1, $2, $3, $4)
                """,
                values,
            )

    async def _load_items(self, cart_id: int) -> list[CartItem]:
        rows = await self._conn.fetch(
            """
            SELECT item_id, quantity, unit_price
            FROM cart_items
            WHERE cart_id = $1
            """,
            cart_id,
        )
        return [
            CartItem(
                item_id=row["item_id"],
                quantity=row["quantity"],
                unit_price=row["unit_price"],
            )
            for row in rows
        ]
