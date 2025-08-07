-- Update existing account names to lowercase
UPDATE accounts SET name = LOWER(name) WHERE name != LOWER(name);

-- Display the results
SELECT 'Accounts updated:' as info;
SELECT id, name FROM accounts ORDER BY id;
