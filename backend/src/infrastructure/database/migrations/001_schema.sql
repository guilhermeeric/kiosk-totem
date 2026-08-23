-- liquibase formatted sql

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
CREATE TABLE items (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL
);

-- changeset totem:5
CREATE TABLE carts (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE
);

-- changeset totem:6
CREATE TABLE cart_items (
    cart_id BIGINT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,  -- snapshot at add time
    PRIMARY KEY (cart_id, item_id)
);

-- changeset totem:7
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

-- rollback DROP TABLE payments, order_items, orders, cart_items, carts, items CASCADE;
-- rollback DROP TYPE payment_status, order_status, order_type;
