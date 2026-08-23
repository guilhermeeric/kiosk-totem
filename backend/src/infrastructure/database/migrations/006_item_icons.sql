-- changeset totem:13
-- Item icons: the DB stores a KEY (like an image reference); the backend
-- resolves it to a renderable glyph (see src/http/icons.py). Future real
-- photos replace the key's resolution, not the schema.
ALTER TABLE items ADD COLUMN icon VARCHAR(50) NOT NULL DEFAULT 'plate';

UPDATE items SET icon = 'coffee' WHERE name = 'Coffee';
UPDATE items SET icon = 'iced-tea' WHERE name = 'Iced Tea';
UPDATE items SET icon = 'lemonade' WHERE name = 'Lemonade';
UPDATE items SET icon = 'chocolate-cake' WHERE name = 'Chocolate Cake';
UPDATE items SET icon = 'cheesecake' WHERE name = 'Cheesecake';
UPDATE items SET icon = 'cookie' WHERE name = 'Chocolate Chip Cookie';
UPDATE items SET icon = 'burger' WHERE name = 'Classic Burger';
UPDATE items SET icon = 'wrap' WHERE name = 'Chicken Wrap';
UPDATE items SET icon = 'fries' WHERE name = 'French Fries';

-- rollback ALTER TABLE items DROP COLUMN icon;
