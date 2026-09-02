-- liquibase formatted sql
--
-- Seed menu. icon is the glyph key (see 001_schema.sql); stock is left to the
-- column default (20), the same starting inventory every item gets.

-- changeset totem:13
INSERT INTO items (name, price, category, icon) VALUES
    ('Coffee', 2.50, 'beverages', 'coffee'),
    ('Iced Tea', 2.00, 'beverages', 'iced-tea'),
    ('Lemonade', 2.50, 'beverages', 'lemonade'),
    ('Chocolate Cake', 4.50, 'sweet', 'chocolate-cake'),
    ('Cheesecake', 5.00, 'sweet', 'cheesecake'),
    ('Chocolate Chip Cookie', 1.50, 'sweet', 'cookie'),
    ('Classic Burger', 9.99, 'savory', 'burger'),
    ('Chicken Wrap', 8.50, 'savory', 'wrap'),
    ('French Fries', 3.50, 'savory', 'fries');

-- rollback DELETE FROM items WHERE category IN ('beverages', 'sweet', 'savory');
