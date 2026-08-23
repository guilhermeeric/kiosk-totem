"""HTTP layer: owns the FastAPI application instance and routes."""

from contextlib import asynccontextmanager

import asyncpg
from fastapi import Depends, FastAPI, Path

from src.domain.payment import PaymentMethod
from src.http.exceptions import register_exception_handlers
from src.http.schemas.cart import (
    CartItemRequest,
    CartResponse,
    CreateCartRequest,
    UpdateQuantityRequest,
)
from src.http.schemas.item import ItemResponse
from src.http.schemas.order import (
    CheckoutRequest,
    CreatePaymentRequest,
    OrderResponse,
    PaymentResponse,
)
from src.infrastructure.database import (
    PostgresCartRepository,
    PostgresItemRepository,
    PostgresOrderRepository,
    PostgresPaymentRepository,
    close_pool,
    get_connection,
    get_pool,
)
from src.usecases.add_cart_item import AddCartItem
from src.usecases.checkout import Checkout
from src.usecases.create_cart import CreateCart
from src.usecases.create_payment_attempt import CreatePaymentAttempt
from src.usecases.get_cart import GetCart
from src.usecases.get_order import GetOrder
from src.usecases.list_items import ListItems
from src.usecases.remove_cart_item import RemoveCartItem
from src.usecases.update_cart_item import UpdateCartItem


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database connection pool on startup, close it on shutdown."""
    await get_pool()
    yield
    await close_pool()


app = FastAPI(
    title="totem-checkout backend",
    description="Checkout backend for totem-checkout.",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

_SessionPath = Path(min_length=1, max_length=255)


def _repos(conn: asyncpg.Connection) -> dict:
    return {
        "cart": PostgresCartRepository(conn),
        "item": PostgresItemRepository(conn),
        "order": PostgresOrderRepository(conn),
        "payment": PostgresPaymentRepository(conn),
    }


# ---- System ----


@app.get("/", tags=["system"], summary="Hello-world root endpoint")
def root() -> dict:
    return {"message": "Hello, world!"}


@app.get("/health", tags=["system"], summary="Simple health check")
def health() -> dict:
    return {"status": "ok"}


# ---- Items (menu) ----


@app.get("/items", response_model=list[ItemResponse], tags=["items"], summary="List menu items")
async def list_items(conn: asyncpg.Connection = Depends(get_connection)) -> list[ItemResponse]:
    repo = _repos(conn)["item"]
    items = await ListItems(repo).execute()
    return [ItemResponse.from_domain(item) for item in items]


# ---- Carts ----


@app.post(
    "/carts",
    response_model=CartResponse,
    status_code=201,
    tags=["carts"],
    summary="Start a new session cart",
)
async def create_cart(
    payload: CreateCartRequest,
    conn: asyncpg.Connection = Depends(get_connection),
) -> CartResponse:
    input_ = payload.to_domain()
    cart = await CreateCart(_repos(conn)["cart"]).execute(input_.session_id)
    return CartResponse.from_domain(cart)


@app.get(
    "/carts/{session_id}", response_model=CartResponse, tags=["carts"], summary="Review a cart"
)
async def get_cart(
    session_id: str = _SessionPath,
    conn: asyncpg.Connection = Depends(get_connection),
) -> CartResponse:
    cart = await GetCart(_repos(conn)["cart"]).execute(session_id)
    return CartResponse.from_domain(cart)


@app.put(
    "/carts/{session_id}/items",
    response_model=CartResponse,
    tags=["carts"],
    summary="Add an item to a cart",
)
async def add_cart_item(
    payload: CartItemRequest,
    session_id: str = _SessionPath,
    conn: asyncpg.Connection = Depends(get_connection),
) -> CartResponse:
    input_ = payload.to_domain()
    repos = _repos(conn)
    async with conn.transaction():
        cart = await AddCartItem(repos["cart"], repos["item"]).execute(
            session_id, input_.item_id, input_.quantity
        )
    return CartResponse.from_domain(cart)


@app.delete(
    "/carts/{session_id}/items/{item_id}",
    response_model=CartResponse,
    tags=["carts"],
    summary="Remove an item from a cart",
)
async def remove_cart_item(
    item_id: int,
    session_id: str = _SessionPath,
    conn: asyncpg.Connection = Depends(get_connection),
) -> CartResponse:
    async with conn.transaction():
        cart = await RemoveCartItem(_repos(conn)["cart"]).execute(session_id, item_id)
    return CartResponse.from_domain(cart)


@app.patch(
    "/carts/{session_id}/items/{item_id}",
    response_model=CartResponse,
    tags=["carts"],
    summary="Change item quantity (0 removes)",
)
async def update_cart_item(
    payload: UpdateQuantityRequest,
    item_id: int,
    session_id: str = _SessionPath,
    conn: asyncpg.Connection = Depends(get_connection),
) -> CartResponse:
    input_ = payload.to_domain()
    async with conn.transaction():
        cart = await UpdateCartItem(_repos(conn)["cart"]).execute(
            session_id, item_id, input_.quantity
        )
    return CartResponse.from_domain(cart)


# ---- Orders ----


@app.post(
    "/orders",
    response_model=OrderResponse,
    status_code=201,
    tags=["orders"],
    summary="Checkout a cart into an order",
)
async def create_order(
    payload: CheckoutRequest,
    conn: asyncpg.Connection = Depends(get_connection),
) -> OrderResponse:
    input_ = payload.to_domain()
    repos = _repos(conn)
    async with conn.transaction():
        order = await Checkout(repos["cart"], repos["order"], repos["payment"]).execute(
            input_.session_id,
            input_.customer_name,
            input_.order_type,
            input_.payment_method,
        )
    return OrderResponse.from_domain(order)


@app.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    tags=["orders"],
    summary="Fetch an order with its payment attempts",
)
async def get_order(
    order_id: int,
    conn: asyncpg.Connection = Depends(get_connection),
) -> OrderResponse:
    repos = _repos(conn)
    order = await GetOrder(repos["order"], repos["payment"]).execute(order_id)
    return OrderResponse.from_domain(order)


# ---- Payments ----


@app.post(
    "/orders/{order_id}/payments",
    response_model=PaymentResponse,
    status_code=201,
    tags=["payments"],
    summary="Create a payment attempt (simulated)",
)
async def create_payment(
    payload: CreatePaymentRequest,
    order_id: int,
    conn: asyncpg.Connection = Depends(get_connection),
) -> PaymentResponse:
    method: PaymentMethod = payload.to_domain()
    repos = _repos(conn)
    payment = await CreatePaymentAttempt(repos["order"], repos["payment"]).execute(order_id, method)
    return PaymentResponse.from_domain(payment)
