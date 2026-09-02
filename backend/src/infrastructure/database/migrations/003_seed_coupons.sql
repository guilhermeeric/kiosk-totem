-- liquibase formatted sql
--
-- Seed a demo coupon. Expiry is 30 days from migration run so the code demos
-- the expired path naturally instead of living forever.

-- changeset totem:14
INSERT INTO coupons (coupon_code, percent, expiry_time, quantity) VALUES
    ('WELCOME10', 10, CURRENT_TIMESTAMP + INTERVAL '30 days', 100);

-- rollback DELETE FROM coupons WHERE coupon_code = 'WELCOME10';
