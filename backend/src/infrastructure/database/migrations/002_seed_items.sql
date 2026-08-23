-- liquibase formatted sql

-- changeset totem:10
INSERT INTO items (name, price, category) VALUES
    ('Coffee', 2.50, 'beverages'),
    ('Iced Tea', 2.00, 'beverages'),
    ('Lemonade', 2.50, 'beverages'),
    ('Chocolate Cake', 4.50, 'sweet'),
    ('Cheesecake', 5.00, 'sweet'),
    ('Chocolate Chip Cookie', 1.50, 'sweet'),
    ('Classic Burger', 9.99, 'savory'),
    ('Chicken Wrap', 8.50, 'savory'),
    ('French Fries', 3.50, 'savory');

-- rollback DELETE FROM items WHERE category IN ('beverages', 'sweet', 'savory');
