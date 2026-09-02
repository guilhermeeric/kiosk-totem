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
            "SELECT id, session_id, handed_off_at, coupon_code, coupon_discount "
            "FROM carts WHERE session_id = $1 FOR UPDATE",
            session_id,
        )
        if not row:
            return None

        cart = Cart(
            id=row["id"],
            session_id=row["session_id"],
            handed_off_at=row["handed_off_at"],
            coupon_code=row["coupon_code"],
            coupon_discount=row["coupon_discount"],
        )
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
                "INSERT INTO carts (session_id, coupon_code, coupon_discount) "
                "VALUES ($1, $2, $3) RETURNING id",
                cart.session_id,
                cart.coupon_code,
                cart.coupon_discount,
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

    async def mark_handed_off(self, cart_id: int) -> None:
        """Record that the session was handed off to another device (QR).

        One-way latch: a session can be handed off at most once. The conditional
        UPDATE is atomic, so concurrent adoptions serialize at the row — the
        second caller gets 0 rows and raises.
        """
        result = await self._conn.execute(
            """
            UPDATE carts SET handed_off_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND handed_off_at IS NULL
            """,
            cart_id,
        )
        if result == "UPDATE 0":
            raise ValueError(f"Cart {cart_id} already handed off")

    async def update(self, cart: Cart) -> None:
        """
        Update an existing cart and replace all its items.
        Cart.id must not be None.
        """
        if cart.id is None:
            raise ValueError("Cannot update a cart without an ID. Use create() instead.")
        # Update cart session_id (though it rarely changes) plus coupon state
        result = await self._conn.execute(
            "UPDATE carts SET session_id = $1, coupon_code = $2, coupon_discount = $3 "
            "WHERE id = $4",
            cart.session_id,
            cart.coupon_code,
            cart.coupon_discount,
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
