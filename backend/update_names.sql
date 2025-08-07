-- Update existing category names to lowercase
UPDATE categories SET name = LOWER(name) WHERE name != LOWER(name);

-- Update existing subcategory names to lowercase
UPDATE sub_categories SET name = LOWER(name) WHERE name != LOWER(name);

-- Display the results
SELECT 'Categories updated:' as info;
SELECT id, name FROM categories ORDER BY id;

SELECT 'Subcategories updated:' as info;
SELECT id, name FROM sub_categories ORDER BY id;
