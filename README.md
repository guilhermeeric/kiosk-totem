# Totem Checkout

A self-service checkout for a fast-food kiosk. A customer walks up to a screen, browses the menu, builds an order, pays, and the kitchen gets it. The purchase flow runs end to end, from selecting items to the customer picking up a ready order.

## Quickstart

Requires Docker. From the repo root:

```bash
make up   # builds and starts postgres + liquibase migrations + backend + frontend
```

The first boot builds the images and installs frontend dependencies; give it a few minutes. Then open:

| Service | URL |
|---|---|
| Kiosk (start → menu → cart → checkout) | http://localhost:5173 |
| Kitchen | http://localhost:5173/kitchen |
| Customer display (visor) | http://localhost:5173/visor |
| Backend API | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |

The frontend runs with `VITE_DEBUG=true`: the payment terminal lets you pick the simulated outcome (approved / declined / network error), and the handoff and receipt screens show a **Test in browser (new tab)** button that emulates a second device. Each tab has its own session, so tabs behave like separate devices.

`make reset` stops the stack and wipes the database volume.

## User journeys

### Customer

- Browse items by category
- Add and remove items; prices are snapshotted when an item is added, so catalog changes never touch an existing cart
- Checkout and pay (simulated)
- Receive an order number
- Track the order live on the phone: the status bar advances as the kitchen moves the order
- Optionally transfer the cart from the totem to a phone with a QR code instead of starting over

### Kiosk worker

- See paid orders in the kitchen queue, split into new / preparing / ready
- See exactly what needs to be prepared (line items)
- Move orders through the status flow: start preparing → done → picked up
- The customer display shows the current ready order for pickup

## Walkthroughs

### 1. Order, kitchen, pickup (the main path)

1. Open http://localhost:5173 and press **Start**.
2. Add a few items, review the cart, and check out. Enter a name, pick eat-in or takeaway, and pay. The simulated terminal approves by default.
3. The receipt shows the order number and a 40-second countdown.
4. Open http://localhost:5173/kitchen in another tab: the order sits in **New**. Click **Start preparing**, then **Done**, then **Picked up**.
5. Open http://localhost:5173/visor: while the order is READY, the display shows the number waiting for pickup.

### 2. Track on the phone

1. After checkout, the receipt shows a QR code pointing at `http://localhost:5173/track/<order-id>`.
2. Click **Test in browser (new tab)** — or scan the QR with a phone on the same network.
3. The tracking screen polls every 5 seconds. Advance the order in the kitchen tab and watch the progress bar move on the phone.

### 3. Hand off the cart to a phone

1. On the kiosk, press **Continue on phone**, then confirm.
2. Open the handoff link in a new tab (debug button) or scan the QR: the phone adopts the cart session, and the totem resets immediately.
3. Keep building the cart on the phone and check out there. The phone's receipt shows a direct track link — no self-scan.

### 4. Failed payment

1. In debug mode the payment terminal offers **Declined** and **Network error**.
2. Pick **Declined**: the checkout fails and no order is created — the transaction rolls back, including stock consumption.
3. **Try again** with **Approved**: the order is created, paid, and sent to the kitchen.

### 5. Inventory limits

1. Add more of an item than the current stock. The cart flags the line ("Only N left").
2. Checkout refuses until the cart is adjusted. The backend re-checks stock atomically at payment, so two customers racing for the last unit cannot oversell it.

## Why these journeys

The critical path is the complete purchase outcome, not payment. An order that stops at "paid" leaves the customer standing at the counter; the kitchen flow and the customer display exist to finish the journey.

The QR handoff comes from the customer being in a hurry: they can leave the physical totem and continue with the same cart on their phone. The cart stays server-side; the QR only transfers the session.

## Architecture

Three principles: model the product in the code, keep dependencies flowing inward, and reduce complexity through information hiding.

### Domain modeling

Business concepts and rules are modeled explicitly:

- A cart item stores the price at the time it was added
- Inventory cannot go negative
- An order has explicit lifecycle transitions (pending → preparing → ready → completed, plus cancel)
- An order can have several payment attempts, but only one successful payment

Domain logic is pure Python — no I/O, no framework imports — so the rules are testable without a database.

### Dependency direction

```
HTTP / Database
      ↓
   Use cases
      ↓
    Domain
```

Infrastructure concerns (FastAPI, asyncpg) stay outside the core business code. Use cases depend on repository interfaces; the Postgres adapters implement them. That seam is what makes the use cases unit-testable.

### Complexity management

Modules hide meaningful complexity behind small interfaces. Checkout, for example, is one operation that hides cart validation, stock consumption, order creation, payment creation, and the transaction that makes them atomic. Abstractions only exist where they earn their keep — no speculative interfaces.

## Project structure

```
backend/src/
├── domain/               # Business concepts and rules (entities, enums, repo interfaces)
├── usecases/             # Application operations (one class per use case, .execute())
├── infrastructure/
│   └── database/         # Postgres adapters + Liquibase migrations
└── http/                 # FastAPI app and schemas

frontend/src/
├── api/                  # Typed HTTP client
├── components/           # Reusable UI components
├── composables/          # Server-state hooks (TanStack Query)
├── domain/               # Frontend domain logic (money, order status, stock)
├── router/
└── views/                # Route-level screens
```

## Data and business rules

**Price snapshots.** Cart and order items store the price at the time they were added. Updating the catalog price does not change existing carts or orders.

**Inventory.** Stock is consumed during checkout, inside the same transaction that creates the order. A `CHECK (stock >= 0)` constraint backs it up at the database level, and `SELECT ... FOR UPDATE` serializes concurrent checkouts so exactly one can take the last unit.

**Payments.** Multiple attempts can exist for an order; the database enforces at most one successful one:

```sql
CREATE UNIQUE INDEX one_paid_attempt_per_order
ON payments(order_id) WHERE status = 'PAID';
```

A retried payment that hits that index returns the existing paid attempt — double-pay is idempotent.

## API contract

The backend's OpenAPI spec (`openapi.json`, committed at the repo root) is the contract. The frontend's TypeScript types are generated from it:

```
FastAPI → OpenAPI → Generated TypeScript types (npm run generate:api)
```

## Stack

Backend: Python, FastAPI, asyncpg, PostgreSQL, Liquibase, segno (QR)

Frontend: Vue 3, TypeScript, Vite, Tailwind CSS, TanStack Query, Vue Router, Lucide

## Scope

Intentionally not implemented:

- Authentication and customer accounts (the session id is the capability; the totem is a public device)
- WebSockets / push notifications (the kitchen, visor, and tracking screens poll instead)
- Complex kitchen workflows (routing, multi-tenant, refunds)

None of these were needed to complete the journeys above. Polling is a few lines of `refetchInterval` and matches the pace of a kitchen — real-time infrastructure would have been a worse trade.
