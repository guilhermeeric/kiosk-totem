-- liquibase formatted sql
--
-- Final schema in one pass. This changelog is the project's single source of
-- truth for the database shape: enums, tables (with every column they will
-- ever carry), and the invariant indexes that guard the domain. It was
-- consolidated from the incremental changesets of the original build so a
-- fresh clone converges on the exact same schema without replaying the
-- create/alter churn. Coupons were woven in in place (AGENTS: no deployed DB,
-- edit + reset), renumbered contiguously.

-- changeset totem:1
CREATE TYPE order_type AS ENUM (
    'EAT_IN',
    'TAKEAWAY'
);

-- rollback DROP TYPE order_type;

-- changeset totem:2
CREATE TYPE order_status AS ENUM (
    'PENDING',
    'PREPARING',
    'READY',
    'COMPLETED',
    'CANCELLED'
);

-- rollback DROP TYPE order_status;

-- changeset totem:3
CREATE TYPE payment_status AS ENUM (
    'PENDING',
    'PAID',
    'FAILED'
);

-- rollback DROP TYPE payment_status;

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

-- rollback DROP TABLE items;

-- changeset totem:5
-- Coupon = operator-issued discount code. expiry_time is the lifecycle end;
-- there is no delete path, so expired rows simply stop validating at apply.
-- percent is the discount off the cart subtotal (10 = 10% off); bounded to
-- (0, 100] so the granted discount can never exceed the cart total.
-- quantity is the remaining paid redemptions (items.stock pattern): the
-- checkout transaction decrements it once per paid order, after payment.
CREATE TABLE coupons (
    coupon_code VARCHAR(255) PRIMARY KEY,
    percent INTEGER NOT NULL,
    expiry_time TIMESTAMP NOT NULL,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT coupons_percent_in_range CHECK (percent > 0 AND percent <= 100),
    CONSTRAINT coupons_quantity_non_negative CHECK (quantity >= 0)
);

-- rollback DROP TABLE coupons;

-- changeset totem:6
-- handed_off_at is the QR-handoff latch: when the phone adopts the session it
-- marks the cart so the totem can reset immediately instead of waiting out its
-- grace period. NULL until handed off.
-- coupon_code references the coupon applied to this cart; carts are transient,
-- so the FK is free integrity. coupon_percent is the coupon's percent
-- snapshotted at apply (10 = 10% off); the granted money discount is computed
-- from the live subtotal in the domain, so it can never exceed the cart total.
CREATE TABLE carts (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    handed_off_at TIMESTAMP NULL,
    coupon_code VARCHAR(255) NULL REFERENCES coupons(coupon_code),
    coupon_percent INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- rollback DROP TABLE carts;

-- changeset totem:7
CREATE TABLE cart_items (
    cart_id BIGINT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,  -- snapshot at add time
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cart_id, item_id)
);

-- rollback DROP TABLE cart_items;

-- changeset totem:8
-- total is the paid sum; the order_items rows snapshot the full price story
-- (list unit price) so an order line stays self-auditable even if menu prices
-- change later. coupon_code/coupon_discount are the redemption snapshot —
-- plain columns, deliberately NO FK: an order is history and must survive
-- anything the coupons table does. coupon_discount is the discount actually
-- granted at checkout (min(cart snapshot, subtotal)).
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT NOT NULL REFERENCES carts(id),
    customer_name VARCHAR(100) NOT NULL,
    type order_type NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    status order_status NOT NULL DEFAULT 'PENDING',
    coupon_code VARCHAR(255) NULL,
    coupon_discount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- rollback DROP TABLE orders;

-- changeset totem:9
CREATE TABLE order_items (
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, item_id)
);

-- rollback DROP TABLE order_items;

-- changeset totem:10
CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    method VARCHAR(20) NOT NULL,
    status payment_status NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- rollback DROP TABLE payments;

-- changeset totem:11
-- A cart can only be checked out once. Carts are left untouched at checkout
-- (the order snapshots its items), so the invariant lives on orders.
CREATE UNIQUE INDEX one_order_per_cart ON orders(cart_id);

-- rollback DROP INDEX one_order_per_cart;

-- changeset totem:12
-- Only one payment attempt may ever reach PAID per order; the domain stays
-- consistent even under concurrent attempts.
CREATE UNIQUE INDEX one_paid_attempt_per_order ON payments(order_id) WHERE status = 'PAID';

-- rollback DROP INDEX one_paid_attempt_per_order;
