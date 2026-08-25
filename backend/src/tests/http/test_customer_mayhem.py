"""Customer-mayhem API tests: the weird things a person at the kiosk can do.

These exercise the real FastAPI app over ASGI against a real Postgres
(TEST_DATABASE_URL), like the infra tests: create, assert, clean up.
"""

import asyncio
import os
from urllib.parse import quote
from uuid import uuid4

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

# The app reads DATABASE_URL lazily when the pool is first created; point it
# at the same database the infra tests use.
os.environ.setdefault(
    "DATABASE_URL",
    os.getenv("TEST_DATABASE_URL", "postgresql://totem:totem@localhost:5432/totem"),
)

from src.http.app import app  # noqa: E402
from src.infrastructure.database.connection import close_pool, get_pool  # noqa: E402


@pytest.fixture
async def client():
    await get_pool()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await close_pool()


async def _connect() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(os.environ["DATABASE_URL"])
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"database unavailable: {exc}")


async def _new_item(conn: asyncpg.Connection, *, stock: int = 20) -> int:
    row = await conn.fetchrow(
        "INSERT INTO items (name, price, category, stock) VALUES ($1, $2, 'test', $3) RETURNING id",
        f"mayhem-{uuid4().hex[:8]}",
        "5.00",
        stock,
    )
    return row["id"]


async def _new_session_cart(client: AsyncClient, session_id: str | None = None) -> str:
    sid = session_id or uuid4().hex
    resp = await client.post("/carts", json={"session_id": sid})
    assert resp.status_code == 201, resp.text
    return sid


async def _add_item(client: AsyncClient, session_id: str, item_id: int, quantity: int) -> None:
    resp = await client.put(
        f"/carts/{quote(session_id, safe='')}/items",
        json={"item_id": item_id, "quantity": quantity},
    )
    assert resp.status_code == 200, resp.text


def _checkout_body(session_id: str, payment_status: str = "PAID") -> dict:
    return {
        "session_id": session_id,
        "customer_name": "Mayhem Customer",
        "order_type": "EAT_IN",
        "payment_method": "PIX",
        "payment_status": payment_status,
    }


async def _checkout(client: AsyncClient, session_id: str, payment_status: str = "PAID"):
    return await client.post("/orders", json=_checkout_body(session_id, payment_status))


async def _cleanup(
    conn: asyncpg.Connection, *, session_ids: list[str], item_ids: list[int]
) -> None:
    if session_ids:
        await conn.execute(
            "DELETE FROM payments WHERE order_id IN "
            "(SELECT id FROM orders WHERE cart_id IN "
            "(SELECT id FROM carts WHERE session_id = ANY($1::text[])))",
            session_ids,
        )
        await conn.execute(
            "DELETE FROM order_items WHERE order_id IN "
            "(SELECT id FROM orders WHERE cart_id IN "
            "(SELECT id FROM carts WHERE session_id = ANY($1::text[])))",
            session_ids,
        )
        await conn.execute(
            "DELETE FROM orders WHERE cart_id IN "
            "(SELECT id FROM carts WHERE session_id = ANY($1::text[]))",
            session_ids,
        )
        await conn.execute(
            "DELETE FROM cart_items WHERE cart_id IN "
            "(SELECT id FROM carts WHERE session_id = ANY($1::text[]))",
            session_ids,
        )
        await conn.execute(
            "DELETE FROM carts WHERE session_id = ANY($1::text[])",
            session_ids,
        )
    if item_ids:
        await conn.execute("DELETE FROM items WHERE id = ANY($1::bigint[])", item_ids)


async def test_session_id_cannot_inject_sql(client: AsyncClient):
    conn = await _connect()
    try:
        session_id = "'; DROP TABLE items; --"
        items_before = len((await client.get("/items")).json())
        await _new_session_cart(client, session_id)

        # The hostile string is a literal session, and the items table is intact.
        got = await client.get(f"/carts/{quote(session_id, safe='')}")
        assert got.status_code == 200, got.text
        assert got.json()["session_id"] == session_id

        items_after = len((await client.get("/items")).json())
        assert items_after == items_before
    finally:
        await _cleanup(conn, session_ids=[session_id], item_ids=[])
        await conn.close()


async def test_retry_after_decline_completes_the_same_checkout(client: AsyncClient):
    conn = await _connect()
    session_id = uuid4().hex
    item_id = await _new_item(conn, stock=2)
    try:
        await _new_session_cart(client, session_id)
        await _add_item(client, session_id, item_id, 2)

        declined = await _checkout(client, session_id, "FAILED")
        assert declined.status_code == 400, declined.text
        assert "declined" in declined.json()["detail"].lower()

        stock = await conn.fetchval("SELECT stock FROM items WHERE id = $1", item_id)
        assert stock == 2  # nothing was consumed

        paid = await _checkout(client, session_id, "PAID")
        assert paid.status_code == 201, paid.text

        stock = await conn.fetchval("SELECT stock FROM items WHERE id = $1", item_id)
        assert stock == 0
        order_id = await conn.fetchval(
            "SELECT o.id FROM orders o JOIN carts c ON c.id = o.cart_id WHERE c.session_id = $1",
            session_id,
        )
        assert order_id is not None
    finally:
        await _cleanup(conn, session_ids=[session_id], item_ids=[item_id])
        await conn.close()


async def test_concurrent_checkouts_race_for_the_last_unit(client: AsyncClient):
    conn = await _connect()
    item_id = await _new_item(conn, stock=1)
    session_ids = [uuid4().hex, uuid4().hex]
    try:
        for sid in session_ids:
            await _new_session_cart(client, sid)
            await _add_item(client, sid, item_id, 1)

        results = await asyncio.gather(
            _checkout(client, session_ids[0]),
            _checkout(client, session_ids[1]),
        )
        statuses = sorted(r.status_code for r in results)
        assert statuses == [201, 400], [r.text for r in results]

        loser = next(r for r in results if r.status_code == 400)
        assert "left of" in loser.json()["detail"]

        stock = await conn.fetchval("SELECT stock FROM items WHERE id = $1", item_id)
        assert stock == 0

        orders = await conn.fetchval(
            "SELECT count(*) FROM orders o JOIN carts c ON c.id = o.cart_id "
            "WHERE c.session_id = ANY($1::text[])",
            session_ids,
        )
        assert orders == 1
    finally:
        await _cleanup(conn, session_ids=session_ids, item_ids=[item_id])
        await conn.close()


async def test_concurrent_checkout_of_the_same_cart_succeeds_once(client: AsyncClient):
    conn = await _connect()
    session_id = uuid4().hex
    item_id = await _new_item(conn, stock=5)
    try:
        await _new_session_cart(client, session_id)
        await _add_item(client, session_id, item_id, 1)

        results = await asyncio.gather(
            _checkout(client, session_id),
            _checkout(client, session_id),
        )
        statuses = sorted(r.status_code for r in results)
        assert statuses == [201, 400], [r.text for r in results]

        loser = next(r for r in results if r.status_code == 400)
        assert "checked out once" in loser.json()["detail"]

        orders = await conn.fetchval(
            "SELECT count(*) FROM orders o JOIN carts c ON c.id = o.cart_id "
            "WHERE c.session_id = $1",
            session_id,
        )
        assert orders == 1
    finally:
        await _cleanup(conn, session_ids=[session_id], item_ids=[item_id])
        await conn.close()


async def test_handoff_is_a_one_way_latch_via_the_api(client: AsyncClient):
    conn = await _connect()
    session_id = uuid4().hex
    try:
        await _new_session_cart(client, session_id)

        first = await client.post(f"/carts/{quote(session_id, safe='')}/handoff")
        assert first.status_code == 204, first.text

        second = await client.post(f"/carts/{quote(session_id, safe='')}/handoff")
        assert second.status_code == 400, second.text
        assert "handed off" in second.json()["detail"].lower()
    finally:
        await _cleanup(conn, session_ids=[session_id], item_ids=[])
        await conn.close()
