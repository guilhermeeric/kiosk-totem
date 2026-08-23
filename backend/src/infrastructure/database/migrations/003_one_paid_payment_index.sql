-- liquibase formatted sql

-- changeset totem:11
CREATE UNIQUE INDEX one_paid_attempt_per_order ON payments(order_id) WHERE status = 'PAID';

-- rollback DROP INDEX one_paid_attempt_per_order;
