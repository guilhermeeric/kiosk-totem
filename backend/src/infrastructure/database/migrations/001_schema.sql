-- liquibase formatted sql
--
-- Final schema in one pass. This changelog is the project's single source of
-- truth for the database shape: enums, tables (with every column they will
-- ever carry), and the invariant indexes that guard the domain. It was
-- consolidated from the incremental changesets of the original build so a
-- fresh clone converges on the exact same schema without replaying the
-- create/alter churn.

-- changeset totem:1
CREATE TYPE order_type AS ENUM (
    'EAT_IN',
    'TAKEAWAY'
);

-- changeset totem:2
CREATE TYPE order_status AS ENUM (
    'PENDING',
    'PREPARING',
    'READY',
    'COMPLETED',
    'CANCELLED'
);

-- changeset totem:3
CREATE TYPE payment_status AS ENUM (
    'PENDING',
    'PAID',
    'FAILED'
);

-- changeset totem:4
-- icon is a KEY (like an image reference), not a rendering; the backend
-- resolves it to a glyph (src/http/icons.py). Future real photos replace the
-- key's resolution, not the schema.
-- stock is the sellable inventory; the CHECK keeps it non-negative at the DB
-- layer and consume_stock enforces availability atomically at checkout.
CREATE TABLE items (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    icon VARCHAR(50) NOT NULL DEFAULT 'plate',
    stock INTEGER NOT NULL DEFAULT 20,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT items_stock_non_negative CHECK (stock >= 0)
);

-- changeset totem:5
-- handed_off_at is the QR-handoff latch: when the phone adopts the session it
-- marks the cart so the totem can reset immediately instead of waiting out its
-- grace period. NULL until handed off.
CREATE TABLE carts (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    handed_off_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- changeset totem:6
CREATE TABLE cart_items (
    cart_id BIGINT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,  -- snapshot at add time
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cart_id, item_id)
);

-- changeset totem:7
-- total is the paid sum; the order_items rows snapshot the full price story
-- (list unit price) so an order line stays self-auditable even if menu prices
-- change later.
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT NOT NULL REFERENCES carts(id),
    customer_name VARCHAR(100) NOT NULL,
    type order_type NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    status order_status NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- changeset totem:8
CREATE TABLE order_items (
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, item_id)
);

-- changeset totem:9
CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    method VARCHAR(20) NOT NULL,
    status payment_status NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- changeset totem:10
-- A cart can only be checked out once. Carts are left untouched at checkout
-- (the order snapshots its items), so the invariant lives on orders.
CREATE UNIQUE INDEX one_order_per_cart ON orders(cart_id);

-- changeset totem:11
-- Only one payment attempt may ever reach PAID per order; the domain stays
-- consistent even under concurrent attempts.
CREATE UNIQUE INDEX one_paid_attempt_per_order ON payments(order_id) WHERE status = 'PAID';

-- rollback DROP INDEX one_paid_attempt_per_order;
-- rollback DROP INDEX one_order_per_cart;
-- rollback DROP TABLE payments;
-- rollback DROP TABLE order_items;
-- rollback DROP TABLE orders;
-- rollback DROP TABLE cart_items;
-- rollback DROP TABLE carts;
-- rollback DROP TABLE items;
-- rollback DROP TYPE payment_status;
-- rollback DROP TYPE order_status;
-- rollback DROP TYPE order_type;
