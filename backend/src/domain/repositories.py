from abc import ABC, abstractmethod

from src.domain.cart import Cart
from src.domain.item import Item
from src.domain.order import Order, OrderStatus
from src.domain.payment import Payment


class ItemRepository(ABC):
    """Interface for loading and persisting Item aggregates."""

    @abstractmethod
    async def get_by_id(self, item_id: int) -> Item | None:
        """Retrieve an item by its ID. Returns None if not found."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Item]:
        """Retrieve all items in the catalog."""
        ...

    @abstractmethod
    async def consume_stock(self, item_id: int, quantity: int) -> None:
        """Atomically decrement an item's stock at checkout.

        Raises ItemNotFound if the item does not exist, or ValueError if the
        requested quantity exceeds the available stock. The Postgres adapter
        row-locks the item (FOR UPDATE) so concurrent checkouts serialize:
        exactly one can consume the last unit.
        """
        ...

    @abstractmethod
    async def add(self, item: Item) -> None:
        """Insert a new item. Item.id must be None (BIGSERIAL assigns it)."""
        ...

    @abstractmethod
    async def update(self, item: Item) -> None:
        """Update an existing item. Item.id must not be None."""
        ...


class CartRepository(ABC):
    """Interface for loading and persisting Cart aggregates."""

    @abstractmethod
    async def get_by_session_id(self, session_id: str) -> Cart | None:
        """Retrieve a cart with all its items by the session identifier."""
        ...

    @abstractmethod
    async def create(self, cart: Cart) -> None:
        """
        Insert a new cart and its items. Cart.id must be None.
        The database assigns the ID (BIGSERIAL).
        """
        ...

    @abstractmethod
    async def update(self, cart: Cart) -> None:
        """
        Update an existing cart and replace all its items.
        Cart.id must not be None.
        """
        ...

    @abstractmethod
    async def mark_handed_off(self, cart_id: int) -> None:
        """Record that the session was handed off to another device (QR)."""
        ...


class OrderRepository(ABC):
    """Interface for loading and persisting Order aggregates."""

    @abstractmethod
    async def get_by_id(self, order_id: int) -> Order | None:
        """Retrieve an order with its items by its ID."""
        ...

    @abstractmethod
    async def create(self, order: Order) -> None:
        """
        Insert a new order and its items. Order.id must be None.
        The database assigns the ID (BIGSERIAL).

        Raises ValueError if the cart has already been checked out
        (one order per cart, enforced by a unique index).
        """
        ...

    @abstractmethod
    async def update(self, order: Order) -> None:
        """
        Update an existing order and replace all its items.
        Order.id must not be None.
        """
        ...

    @abstractmethod
    async def update_status(self, order_id: int, status: OrderStatus) -> None:
        """Update only the status of an order (kitchen/visor transitions)."""
        ...

    @abstractmethod
    async def list_by_status(self, status: OrderStatus) -> list[Order]:
        """Retrieve all orders matching a given status (e.g., for the kitchen display)."""
        ...


class PaymentRepository(ABC):
    """Interface for persisting Payment attempts of an order."""

    @abstractmethod
    async def create(self, payment: Payment) -> None:
        """Insert a new payment attempt. Payment.id must be None; the database
        assigns the ID (BIGSERIAL).

        A partial unique index allows at most one PAID attempt per order; a
        duplicate insert raises ValueError.
        """
        ...


class UnitOfWork(ABC):
    """Atomic scope for purchase-flow writes; exposes the write repositories.

    Usecases open it with `async with`: the adapter commits on clean exit and
    rolls back on any exception. Tests use FakeUnitOfWork.
    """

    carts: CartRepository
    items: ItemRepository
    orders: OrderRepository
    payments: PaymentRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
