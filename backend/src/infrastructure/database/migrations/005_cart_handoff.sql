-- changeset totem:12
-- QR handoff: when the phone adopts the session, it marks the cart so the
-- totem can reset immediately instead of waiting out its grace period.
ALTER TABLE carts ADD COLUMN handed_off_at TIMESTAMP NULL;

-- rollback ALTER TABLE carts DROP COLUMN handed_off_at;
