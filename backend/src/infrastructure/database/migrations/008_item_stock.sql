-- liquibase formatted sql

-- changeset totem:15
-- Inventory: each item carries its sellable stock. Existing seed items get a
-- starting stock of 20. The CHECK keeps stock non-negative at the DB layer;
-- consume_stock enforces availability atomically at checkout.
ALTER TABLE items ADD COLUMN stock INTEGER NOT NULL DEFAULT 20;
ALTER TABLE items ADD CONSTRAINT items_stock_non_negative CHECK (stock >= 0);

-- rollback ALTER TABLE items DROP CONSTRAINT items_stock_non_negative;
-- rollback ALTER TABLE items DROP COLUMN stock;
