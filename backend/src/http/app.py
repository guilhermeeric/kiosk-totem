"""HTTP layer: owns the FastAPI application instance and routes."""
import asyncpg
from fastapi import Depends, FastAPI

from src.http.schemas.item import ItemResponse
from src.infrastructure.database import (
    PostgresItemRepository,
    close_pool,
    get_connection,
    get_pool,
)
from src.usecases.list_items import ListItems

app = FastAPI(
    title="totem-checkout backend",
    description="Checkout backend for totem-checkout.",
    version="0.1.0",
)


# ---- Lifespan (startup / shutdown) ----

@app.on_event("startup")
async def startup() -> None:
    """Initialize the database connection pool on startup."""
    await get_pool()


@app.on_event("shutdown")
async def shutdown() -> None:
    """Close the database connection pool on shutdown."""
    await close_pool()


# ---- Public endpoints ----

@app.get("/")
def root() -> dict:
    """Hello-world root endpoint."""
    return {"message": "Hello, world!"}


@app.get("/health")
def health() -> dict:
    """Simple health check."""
    return {"status": "ok"}


@app.get("/items", response_model=list[ItemResponse])
async def list_items(
    conn: asyncpg.Connection = Depends(get_connection),
) -> list[ItemResponse]:
    repo = PostgresItemRepository(conn)
    use_case = ListItems(repo)
    items = await use_case.execute()
    return [ItemResponse.from_domain(item) for item in items]
