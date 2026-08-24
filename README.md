# Totem Checkout

A self-service checkout for a fast-food kiosk.

A customer walks up to a screen, browses the menu, builds an order, pays, and the kitchen gets it. The purchase flow runs end to end, from selecting items to the customer picking up a ready order.

## Quickstart

Requires Docker. From the repo root:

```bash
make up
```

This starts PostgreSQL, Liquibase migrations, the backend, and the frontend.

The first boot builds the images and installs frontend dependencies, so give it a few minutes. Then open:

| Service | URL |
|---|---|
| Kiosk | http://localhost:5173 |
| Kitchen | http://localhost:5173/kitchen |
| Customer display | http://localhost:5173/visor |
| Backend API | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |

The frontend runs with `VITE_DEBUG=true`:

- Payment outcomes can be simulated: approved, declined, or network error
- Handoff and receipt screens can emulate a second device in a new tab
- Each tab has its own session

`make reset` stops the stack and wipes the database volume.

## User journeys

### Customer

- Browse items by category
- Build a cart with price snapshots
- Checkout and pay
- Receive an order number
- Track the order on a phone
- Optionally transfer the cart from the totem to a phone with a QR code

### Kiosk worker

- See paid orders in the kitchen queue
- See what needs to be prepared
- Move orders through `PENDING → PREPARING → READY → COMPLETED`
- Show ready orders on the customer display

## Walkthroughs

### Order, kitchen, pickup

1. Open http://localhost:5173 and press **Start**.
2. Add items, review the cart, choose eat-in or takeaway, and pay.
3. The receipt shows the order number.
4. Open http://localhost:5173/kitchen in another tab and move the order through the kitchen flow.
5. Open http://localhost:5173/visor. Ready orders appear on the customer display.

### Track on the phone

After checkout, the receipt contains a QR code pointing to the order tracking page.

Use **Test in browser (new tab)** or scan the QR from another device. The tracking screen polls every 5 seconds and follows the order as the kitchen updates it.

### Hand off the cart

Press **Continue on phone** on the kiosk.

The phone adopts the existing cart session and the totem resets. The customer can continue building the same cart and check out from the phone.

### Failed payment

In debug mode, choose **Declined** or **Network error**.

A failed payment creates no order and rolls back stock consumption. The customer can retry and complete the same checkout.

## Why these journeys

I treated the critical path as the complete purchase outcome, not just payment.

```text
Customer pays
    ↓
Kitchen prepares the order
    ↓
Customer knows it is ready
    ↓
Customer picks it up
```

The kitchen and customer display complete the same journey.

The QR handoff came from the customer being in a hurry. If I had already built a cart, I would not want to remain tied to the physical totem. The cart stays server-side; the QR code transfers the session.

## Architecture

I had three goals when structuring the code:

1. Keep the product model close to the code
2. Keep business decisions independent from framework and database details
3. Add complexity when there is a concrete reason for it

DDD, inward dependency flow, and ideas from *A Philosophy of Software Design* were tools toward those goals.

### Starting from the product

The model grew from questions raised by the journeys:

- Prices can change after an item enters a cart → store price snapshots
- Payments can fail and be retried → model payment attempts
- Payment is not the end of the journey → model preparation and readiness
- A customer may be in a hurry → allow cart handoff

The resulting domain logic is pure Python with no I/O or framework imports.

### Dependency direction

```text
HTTP / Database
      ↓
   Use cases
      ↓
    Domain
```

FastAPI and asyncpg stay outside the business code.

Use cases depend on repository interfaces; PostgreSQL provides the implementation. This keeps persistence details out of application behavior and makes use cases easy to test in isolation.

### Complexity management

I used modules to hide meaningful complexity.

Checkout is one operation that coordinates:

```text
Cart validation
Stock consumption
Order creation
Payment creation
Atomic persistence
```

Callers do not need to understand or coordinate those steps.

Repository interfaces similarly hide SQL, connection handling, and database mapping from use cases.

## Key decisions

### Price snapshots

Cart and order items store the price at the time they were added.

Catalog price changes do not affect existing carts or orders.

### Inventory

Stock is consumed during checkout inside the same transaction that creates the order.

`CHECK (stock >= 0)` protects the database invariant, while `SELECT ... FOR UPDATE` serializes concurrent checkouts so two customers cannot oversell the last unit.

### Payments

An order is created with its payment in the same transaction: PAID, or nothing — a declined payment rolls the checkout back. The database enforces that only one attempt can ever reach PAID:

```sql
CREATE UNIQUE INDEX one_paid_attempt_per_order
ON payments(order_id)
WHERE status = 'PAID';
```

Repeating a PAID attempt returns the existing payment instead of inserting a new one, so the retry path is idempotent.

## Project structure

```text
backend/src/
├── domain/               # Business concepts and rules
├── usecases/             # Application operations
├── infrastructure/
│   └── database/         # Postgres adapters + migrations
└── http/                 # FastAPI delivery layer

frontend/src/
├── api/                  # Typed HTTP client
├── components/           # Reusable UI
├── composables/          # Server state
├── domain/               # Frontend domain logic
├── router/
└── views/                # Route screens
```

## API contract

The backend's `openapi.json` is the API contract.

```text
FastAPI
  ↓
OpenAPI
  ↓
Generated TypeScript types
```

Generate the frontend types with:

```bash
npm run generate:api
```

## Stack

**Backend:** Python, FastAPI, asyncpg, PostgreSQL, Liquibase, Segno

**Frontend:** Vue 3, TypeScript, Vite, Tailwind CSS, TanStack Query, Vue Router, Lucide

## Scope

Intentionally not implemented:

- Authentication and customer accounts
- WebSockets / push notifications
- Complex kitchen routing
- Refunds
- Adding new items from the kiosk
- Discounts

The kitchen, visor, and tracking screens use polling. The update frequency here did not justify adding real-time infrastructure.
