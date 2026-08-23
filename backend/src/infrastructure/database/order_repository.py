import asyncpg

from src.domain.order import Order, OrderItem, OrderStatus, OrderType
from src.domain.repositories import OrderRepository


class PostgresOrderRepository(OrderRepository):
    """PostgreSQL implementation of the OrderRepository interface."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def get_by_id(self, order_id: int) -> Order | None:
        row = await self._conn.fetchrow(
            """
            SELECT
                id, cart_id, customer_name, type, total,
                status, created_at, updated_at
            FROM orders
            WHERE id = $1
            """,
            order_id,
        )
        if not row:
            return None

        order = Order(
            id=row["id"],
            cart_id=row["cart_id"],
            customer_name=row["customer_name"],
            order_type=OrderType(row["type"]),
            total=row["total"],
            status=OrderStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            items=[],  # filled below
        )
        order.items = await self._load_items(order.id)
        return order

    async def create(self, order: Order) -> None:
        """
        Insert a new order and its items.
        Order.id must be None; the database will assign a BIGSERIAL.
        """
        if order.id is not None:
            raise ValueError("Cannot create an order with an existing ID. Use update() instead.")

        # Insert the order
        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO orders (
                    cart_id, customer_name, type, total, status
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, created_at, updated_at
                """,
                order.cart_id,
                order.customer_name,
                order.order_type.value,
                order.total,
                order.status.value,
            )
        except asyncpg.UniqueViolationError:
            # one_order_per_cart: a cart can only be checked out once.
            raise ValueError("A cart can only be checked out once") from None
        if row is None:
            raise ValueError("Order insert returned no row")
        order.id = row["id"]  # Update the domain object
        order.created_at = row["created_at"]
        order.updated_at = row["updated_at"]

        # Insert order items
        if order.items:
            values = [(order.id, oi.item_id, oi.quantity, oi.unit_price) for oi in order.items]
            await self._conn.executemany(
                """
                INSERT INTO order_items (order_id, item_id, quantity, unit_price)
                VALUES ($1, $2, $3, $4)
                """,
                values,
            )

    async def update(self, order: Order) -> None:
        """
        Update an existing order and replace all its items.
        Order.id must not be None.
        """
        if order.id is None:
            raise ValueError("Cannot update an order without an ID. Use create() instead.")

        # Update the order itself
        result = await self._conn.execute(
            """
            UPDATE orders
            SET
                customer_name = $1,
                type = $2,
                total = $3,
                status = $4,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $5
            """,
            order.customer_name,
            order.order_type.value,
            order.total,
            order.status.value,
            order.id,
        )
        if result == "UPDATE 0":
            raise ValueError(f"Order with id {order.id} not found")

        # Replace items (delete old, insert new)
        await self._conn.execute(
            "DELETE FROM order_items WHERE order_id = $1",
            order.id,
        )
        if order.items:
            values = [(order.id, oi.item_id, oi.quantity, oi.unit_price) for oi in order.items]
            await self._conn.executemany(
                """
                INSERT INTO order_items (order_id, item_id, quantity, unit_price)
                VALUES ($1, $2, $3, $4)
                """,
                values,
            )

    async def update_status(self, order_id: int, status: OrderStatus) -> None:
        """Update only the status of an order (kitchen/visor transitions)."""
        await self._conn.execute(
            """
            UPDATE orders
            SET status = $2, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,
            order_id,
            status.value,
        )

    async def list_by_status(self, status: OrderStatus) -> list[Order]:
        rows = await self._conn.fetch(
            """
            SELECT
                id, cart_id, customer_name, type, total,
                status, created_at, updated_at
            FROM orders
            WHERE status = $1
            ORDER BY created_at ASC
            """,
            status.value,
        )

        orders = []
        for row in rows:
            order = Order(
                id=row["id"],
                cart_id=row["cart_id"],
                customer_name=row["customer_name"],
                order_type=OrderType(row["type"]),
                total=row["total"],
                status=OrderStatus(row["status"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                items=[],
            )
            order.items = await self._load_items(order.id)
            orders.append(order)

        return orders

    async def _load_items(self, order_id: int) -> list[OrderItem]:
        rows = await self._conn.fetch(
            """
            SELECT item_id, quantity, unit_price
            FROM order_items
            WHERE order_id = $1
            """,
            order_id,
        )
        return [
            OrderItem(
                item_id=row["item_id"],
                quantity=row["quantity"],
                unit_price=row["unit_price"],
            )
            for row in rows
        ]
