-- liquibase formatted sql

-- changeset totem:14
-- Every table carries created_at/updated_at (orders and payments already did).
-- Existing rows backfill to the migration time via DEFAULT CURRENT_TIMESTAMP.
ALTER TABLE items ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE items ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE carts ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE carts ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE cart_items ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE cart_items ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE order_items ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE order_items ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- rollback ALTER TABLE order_items DROP COLUMN updated_at;
-- rollback ALTER TABLE order_items DROP COLUMN created_at;
-- rollback ALTER TABLE cart_items DROP COLUMN updated_at;
-- rollback ALTER TABLE cart_items DROP COLUMN created_at;
-- rollback ALTER TABLE carts DROP COLUMN updated_at;
-- rollback ALTER TABLE carts DROP COLUMN created_at;
-- rollback ALTER TABLE items DROP COLUMN updated_at;
-- rollback ALTER TABLE items DROP COLUMN created_at;
