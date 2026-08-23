-- liquibase formatted sql

-- changeset totem:12
-- A cart can only be checked out once. Carts are left untouched at checkout
-- (the order snapshots its items), so the invariant lives on orders.
CREATE UNIQUE INDEX one_order_per_cart ON orders(cart_id);

-- rollback DROP INDEX one_order_per_cart;
