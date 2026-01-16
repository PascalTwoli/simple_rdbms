-- Test script for Simple RDBMS
-- Run with: python3 main.py -f test_rdbms.sql

-- ============================================================
-- Test 1: Create tables
-- ============================================================
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    age INTEGER,
    active BOOLEAN
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product TEXT NOT NULL,
    total REAL,
    shipped BOOLEAN
);

-- ============================================================
-- Test 2: Insert data
-- ============================================================
INSERT INTO users (id, name, email, age, active) VALUES (1, 'Alice', 'alice@example.com', 30, true);
INSERT INTO users (id, name, email, age, active) VALUES (2, 'Bob', 'bob@example.com', 25, true);
INSERT INTO users (id, name, email, age, active) VALUES (3, 'Charlie', 'charlie@example.com', 35, false);
INSERT INTO users (id, name, email, age, active) VALUES (4, 'Diana', 'diana@example.com', 28, true);

INSERT INTO orders (id, user_id, product, total, shipped) VALUES (101, 1, 'Laptop', 999.99, true);
INSERT INTO orders (id, user_id, product, total, shipped) VALUES (102, 1, 'Mouse', 29.99, true);
INSERT INTO orders (id, user_id, product, total, shipped) VALUES (103, 2, 'Keyboard', 79.99, false);
INSERT INTO orders (id, user_id, product, total, shipped) VALUES (104, 3, 'Monitor', 349.99, true);
INSERT INTO orders (id, user_id, product, total, shipped) VALUES (105, 2, 'Headphones', 149.99, false);

-- ============================================================
-- Test 3: Basic SELECT
-- ============================================================
SELECT * FROM users;

SELECT name, email FROM users WHERE active = true;

SELECT * FROM users WHERE age > 27 ORDER BY age DESC;

-- ============================================================
-- Test 4: INNER JOIN
-- ============================================================
SELECT u.name, o.product, o.total 
FROM users u 
INNER JOIN orders o ON u.id = o.user_id;

-- ============================================================
-- Test 5: LEFT JOIN
-- ============================================================
SELECT u.name, o.product 
FROM users u 
LEFT JOIN orders o ON u.id = o.user_id;

-- ============================================================
-- Test 6: UPDATE
-- ============================================================
UPDATE users SET active = false WHERE name = 'Bob';

SELECT name, active FROM users;

-- ============================================================
-- Test 7: DELETE
-- ============================================================
DELETE FROM orders WHERE shipped = true;

SELECT * FROM orders;

-- ============================================================
-- Test 8: Complex WHERE
-- ============================================================
SELECT * FROM users WHERE (age > 25 AND active = true) OR name = 'Charlie';

-- ============================================================
-- Test 9: LIKE operator
-- ============================================================
SELECT * FROM users WHERE name LIKE 'A%';

SELECT * FROM users WHERE email LIKE '%@example.com';

-- ============================================================
-- Test 10: NULL handling
-- ============================================================
INSERT INTO users (id, name, age, active) VALUES (5, 'Eve', 22, true);

SELECT * FROM users WHERE email IS NULL;

SELECT * FROM users WHERE email IS NOT NULL;
