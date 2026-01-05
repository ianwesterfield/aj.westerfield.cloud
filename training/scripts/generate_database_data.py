#!/usr/bin/env python3
"""
Database Training Data Generator
Target: ~250 examples for SQL, PostgreSQL, MongoDB, Redis, database design
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for database development.
You help with SQL, database design, query optimization, and working with various databases."""

# =============================================================================
# SQL TASKS
# =============================================================================

BASIC_SQL_TASKS = [
    {
        "instruction": "Select all users from the users table",
        "sql": "SELECT * FROM users;",
        "explanation": "Retrieves all columns and rows from users table"
    },
    {
        "instruction": "Find users with email ending in @gmail.com",
        "sql": "SELECT * FROM users WHERE email LIKE '%@gmail.com';",
        "explanation": "Pattern matching with LIKE; % is wildcard"
    },
    {
        "instruction": "Count total orders by each customer",
        "sql": "SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id;",
        "explanation": "Aggregation with GROUP BY"
    },
    {
        "instruction": "Get orders with customer information",
        "sql": "SELECT o.id, o.total, c.name, c.email FROM orders o JOIN customers c ON o.customer_id = c.id;",
        "explanation": "INNER JOIN links orders to customers"
    },
    {
        "instruction": "Find customers without any orders",
        "sql": "SELECT c.* FROM customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE o.id IS NULL;",
        "explanation": "LEFT JOIN with NULL check finds unmatched rows"
    },
    {
        "instruction": "Get top 10 products by revenue",
        "sql": "SELECT product_id, SUM(quantity * price) as revenue FROM order_items GROUP BY product_id ORDER BY revenue DESC LIMIT 10;",
        "explanation": "Aggregation with ORDER BY and LIMIT"
    },
    {
        "instruction": "Insert a new user",
        "sql": "INSERT INTO users (name, email, created_at) VALUES ('John Doe', 'john@example.com', NOW());",
        "explanation": "INSERT with explicit columns and values"
    },
    {
        "instruction": "Update user email",
        "sql": "UPDATE users SET email = 'newemail@example.com', updated_at = NOW() WHERE id = 123;",
        "explanation": "UPDATE with WHERE clause - always include WHERE!"
    },
    {
        "instruction": "Delete old records",
        "sql": "DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days';",
        "explanation": "DELETE with date arithmetic"
    },
    {
        "instruction": "Select specific columns from users",
        "sql": "SELECT id, name, email FROM users;",
        "explanation": "Selecting only needed columns is more efficient"
    },
    {
        "instruction": "Find users created in the last 7 days",
        "sql": "SELECT * FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days';",
        "explanation": "Date filtering with INTERVAL"
    },
    {
        "instruction": "Sort users by name alphabetically",
        "sql": "SELECT * FROM users ORDER BY name ASC;",
        "explanation": "ORDER BY sorts results, ASC is ascending (default)"
    },
    {
        "instruction": "Get distinct countries from addresses",
        "sql": "SELECT DISTINCT country FROM addresses;",
        "explanation": "DISTINCT removes duplicate values"
    },
    {
        "instruction": "Count total users",
        "sql": "SELECT COUNT(*) as total_users FROM users;",
        "explanation": "COUNT aggregate function"
    },
    {
        "instruction": "Find minimum and maximum prices",
        "sql": "SELECT MIN(price) as lowest, MAX(price) as highest FROM products;",
        "explanation": "MIN and MAX aggregate functions"
    },
    {
        "instruction": "Calculate average order total",
        "sql": "SELECT AVG(total) as avg_order FROM orders;",
        "explanation": "AVG calculates arithmetic mean"
    },
    {
        "instruction": "Sum total sales",
        "sql": "SELECT SUM(total) as total_sales FROM orders WHERE status = 'completed';",
        "explanation": "SUM with WHERE filter"
    },
    {
        "instruction": "Find users with NULL phone number",
        "sql": "SELECT * FROM users WHERE phone IS NULL;",
        "explanation": "Use IS NULL, not = NULL for NULL comparison"
    },
    {
        "instruction": "Find users with name starting with 'John'",
        "sql": "SELECT * FROM users WHERE name LIKE 'John%';",
        "explanation": "LIKE with % wildcard at end"
    },
    {
        "instruction": "Case-insensitive search",
        "sql": "SELECT * FROM users WHERE LOWER(name) LIKE '%john%';",
        "explanation": "Use LOWER() or ILIKE (PostgreSQL) for case-insensitive"
    },
    {
        "instruction": "Filter with multiple conditions",
        "sql": "SELECT * FROM products WHERE price > 100 AND category = 'Electronics' AND stock > 0;",
        "explanation": "Multiple AND conditions must all be true"
    },
    {
        "instruction": "Filter with OR conditions",
        "sql": "SELECT * FROM orders WHERE status = 'pending' OR status = 'processing';",
        "explanation": "OR returns rows matching any condition"
    },
    {
        "instruction": "Use IN for multiple values",
        "sql": "SELECT * FROM orders WHERE status IN ('pending', 'processing', 'shipped');",
        "explanation": "IN is cleaner than multiple ORs"
    },
    {
        "instruction": "Filter with BETWEEN range",
        "sql": "SELECT * FROM products WHERE price BETWEEN 50 AND 100;",
        "explanation": "BETWEEN is inclusive of both endpoints"
    },
    {
        "instruction": "Combine columns in output",
        "sql": "SELECT first_name || ' ' || last_name as full_name FROM users;",
        "explanation": "Concatenation with ||, alias with AS"
    },
    {
        "instruction": "Conditional output with CASE",
        "sql": "SELECT name, price, CASE WHEN price < 50 THEN 'Budget' WHEN price < 100 THEN 'Mid' ELSE 'Premium' END as tier FROM products;",
        "explanation": "CASE for conditional column values"
    },
    {
        "instruction": "Get first 20 results with offset",
        "sql": "SELECT * FROM products ORDER BY created_at DESC LIMIT 20 OFFSET 40;",
        "explanation": "Pagination: page 3 with 20 per page"
    },
    {
        "instruction": "Group by multiple columns",
        "sql": "SELECT category, status, COUNT(*) FROM products GROUP BY category, status;",
        "explanation": "GROUP BY with multiple dimensions"
    },
    {
        "instruction": "Filter groups with HAVING",
        "sql": "SELECT category, COUNT(*) as count FROM products GROUP BY category HAVING COUNT(*) > 10;",
        "explanation": "HAVING filters after GROUP BY aggregation"
    },
    {
        "instruction": "Insert multiple rows",
        "sql": "INSERT INTO products (name, price, category) VALUES ('Product A', 19.99, 'Electronics'), ('Product B', 29.99, 'Electronics'), ('Product C', 9.99, 'Books');",
        "explanation": "Batch insert is more efficient"
    },
    {
        "instruction": "Create table with constraints",
        "sql": "CREATE TABLE products (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL, price DECIMAL(10,2) CHECK (price > 0), category VARCHAR(100), created_at TIMESTAMP DEFAULT NOW());",
        "explanation": "Constraints ensure data integrity"
    },
    {
        "instruction": "Add foreign key constraint",
        "sql": "ALTER TABLE orders ADD CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE;",
        "explanation": "Foreign key with cascade delete"
    },
    {
        "instruction": "Create unique constraint",
        "sql": "ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);",
        "explanation": "Unique constraint prevents duplicates"
    },
    {
        "instruction": "Add column to existing table",
        "sql": "ALTER TABLE users ADD COLUMN phone VARCHAR(20);",
        "explanation": "ALTER TABLE modifies table structure"
    },
    {
        "instruction": "Drop column from table",
        "sql": "ALTER TABLE users DROP COLUMN phone;",
        "explanation": "Removes column and all its data"
    },
    {
        "instruction": "Rename column",
        "sql": "ALTER TABLE users RENAME COLUMN name TO full_name;",
        "explanation": "Renames column without affecting data"
    },
    {
        "instruction": "Create index for faster queries",
        "sql": "CREATE INDEX idx_users_email ON users(email);",
        "explanation": "Index speeds up WHERE clause lookups"
    },
    {
        "instruction": "Create composite index",
        "sql": "CREATE INDEX idx_orders_customer_date ON orders(customer_id, created_at);",
        "explanation": "Multi-column index for combined queries"
    },
    {
        "instruction": "Truncate table",
        "sql": "TRUNCATE TABLE logs;",
        "explanation": "Faster than DELETE, resets auto-increment"
    },
    {
        "instruction": "Copy data between tables",
        "sql": "INSERT INTO archive_orders SELECT * FROM orders WHERE created_at < '2023-01-01';",
        "explanation": "INSERT with SELECT copies matching rows"
    },
    {
        "instruction": "Create view",
        "sql": "CREATE VIEW active_users AS SELECT * FROM users WHERE active = true AND last_login > NOW() - INTERVAL '30 days';",
        "explanation": "View is a saved query that acts like table"
    },
    {
        "instruction": "Get current timestamp",
        "sql": "SELECT NOW(), CURRENT_TIMESTAMP, CURRENT_DATE, CURRENT_TIME;",
        "explanation": "Various date/time functions"
    },
    {
        "instruction": "Extract date parts",
        "sql": "SELECT EXTRACT(YEAR FROM created_at) as year, EXTRACT(MONTH FROM created_at) as month, EXTRACT(DAY FROM created_at) as day FROM orders;",
        "explanation": "EXTRACT gets components from timestamps"
    },
    {
        "instruction": "Format date",
        "sql": "SELECT TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as formatted FROM orders;",
        "explanation": "TO_CHAR formats timestamps as strings"
    },
    {
        "instruction": "Round numbers",
        "sql": "SELECT ROUND(price, 2) as rounded_price, CEIL(quantity) as ceiling, FLOOR(rating) as floored FROM products;",
        "explanation": "ROUND, CEIL, FLOOR for number rounding"
    },
    {
        "instruction": "Handle NULL values",
        "sql": "SELECT name, COALESCE(phone, 'No phone') as phone FROM users;",
        "explanation": "COALESCE returns first non-NULL value"
    },
    {
        "instruction": "String length",
        "sql": "SELECT name, LENGTH(name) as name_length FROM users;",
        "explanation": "LENGTH returns character count"
    },
    {
        "instruction": "Substring extraction",
        "sql": "SELECT SUBSTRING(description FROM 1 FOR 100) as preview FROM posts;",
        "explanation": "SUBSTRING extracts portion of string"
    },
    {
        "instruction": "Replace text",
        "sql": "UPDATE users SET email = REPLACE(email, '@old.com', '@new.com') WHERE email LIKE '%@old.com';",
        "explanation": "REPLACE substitutes text in string"
    },
    {
        "instruction": "Trim whitespace",
        "sql": "SELECT TRIM(name), LTRIM(name), RTRIM(name) FROM users;",
        "explanation": "TRIM removes leading/trailing whitespace"
    },
]

ADVANCED_SQL_TASKS = [
    {
        "instruction": "Get running total of sales by date",
        "sql": """SELECT 
  date,
  daily_sales,
  SUM(daily_sales) OVER (ORDER BY date) as running_total
FROM (
  SELECT DATE(created_at) as date, SUM(total) as daily_sales
  FROM orders
  GROUP BY DATE(created_at)
) daily;""",
        "explanation": "Window function for cumulative sum"
    },
    {
        "instruction": "Find duplicate email addresses",
        "sql": """SELECT email, COUNT(*) as count
FROM users
GROUP BY email
HAVING COUNT(*) > 1;""",
        "explanation": "HAVING filters after GROUP BY"
    },
    {
        "instruction": "Get users with their order count and total spend",
        "sql": """SELECT 
  u.id,
  u.name,
  COUNT(o.id) as order_count,
  COALESCE(SUM(o.total), 0) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;""",
        "explanation": "LEFT JOIN with aggregation, COALESCE handles NULL"
    },
    {
        "instruction": "Rank products by sales within each category",
        "sql": """SELECT 
  category_id,
  product_name,
  sales,
  RANK() OVER (PARTITION BY category_id ORDER BY sales DESC) as rank
FROM products;""",
        "explanation": "PARTITION BY creates groups for window function"
    },
    {
        "instruction": "Get hierarchical data (employee-manager)",
        "sql": """WITH RECURSIVE org_chart AS (
  SELECT id, name, manager_id, 1 as level
  FROM employees
  WHERE manager_id IS NULL
  
  UNION ALL
  
  SELECT e.id, e.name, e.manager_id, oc.level + 1
  FROM employees e
  JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT * FROM org_chart ORDER BY level, name;""",
        "explanation": "Recursive CTE for tree/hierarchy traversal"
    },
    {
        "instruction": "Find gaps in sequence of IDs",
        "sql": """SELECT prev_id + 1 as gap_start, id - 1 as gap_end
FROM (
  SELECT id, LAG(id) OVER (ORDER BY id) as prev_id
  FROM orders
) gaps
WHERE id - prev_id > 1;""",
        "explanation": "LAG window function to compare consecutive rows"
    },
    {
        "instruction": "Pivot monthly sales by product",
        "sql": """SELECT 
  product_id,
  SUM(CASE WHEN EXTRACT(MONTH FROM date) = 1 THEN amount ELSE 0 END) as jan,
  SUM(CASE WHEN EXTRACT(MONTH FROM date) = 2 THEN amount ELSE 0 END) as feb,
  SUM(CASE WHEN EXTRACT(MONTH FROM date) = 3 THEN amount ELSE 0 END) as mar
FROM sales
WHERE EXTRACT(YEAR FROM date) = 2024
GROUP BY product_id;""",
        "explanation": "Conditional aggregation creates pivot table"
    },
    {
        "instruction": "Upsert (insert or update)",
        "sql": """INSERT INTO users (id, email, name)
VALUES (1, 'john@example.com', 'John')
ON CONFLICT (id) DO UPDATE SET
  email = EXCLUDED.email,
  name = EXCLUDED.name,
  updated_at = NOW();""",
        "explanation": "PostgreSQL upsert with ON CONFLICT"
    },
    {
        "instruction": "Calculate moving average",
        "sql": """SELECT 
  date,
  value,
  AVG(value) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg_7day
FROM daily_metrics;""",
        "explanation": "Window function with ROWS frame for moving average"
    },
    {
        "instruction": "Get first and last value per group",
        "sql": """SELECT DISTINCT
  customer_id,
  FIRST_VALUE(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) as first_order,
  LAST_VALUE(order_date) OVER (PARTITION BY customer_id ORDER BY order_date 
    RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as last_order
FROM orders;""",
        "explanation": "FIRST_VALUE and LAST_VALUE with proper window frame"
    },
    {
        "instruction": "Calculate percentage of total",
        "sql": """SELECT 
  category,
  sales,
  ROUND(100.0 * sales / SUM(sales) OVER (), 2) as pct_of_total
FROM category_sales;""",
        "explanation": "Empty OVER() calculates across all rows"
    },
    {
        "instruction": "Identify consecutive date ranges",
        "sql": """WITH numbered AS (
  SELECT date, date - ROW_NUMBER() OVER (ORDER BY date)::int as grp
  FROM login_dates
)
SELECT MIN(date) as range_start, MAX(date) as range_end, COUNT(*) as consecutive_days
FROM numbered
GROUP BY grp
ORDER BY range_start;""",
        "explanation": "Island detection using difference between date and row number"
    },
    {
        "instruction": "Get top N per group",
        "sql": """SELECT * FROM (
  SELECT 
    category,
    product_name,
    revenue,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) as rn
  FROM products
) ranked
WHERE rn <= 3;""",
        "explanation": "Subquery with ROW_NUMBER for top-N per group"
    },
    {
        "instruction": "Compare current row to previous row",
        "sql": """SELECT 
  date,
  revenue,
  LAG(revenue) OVER (ORDER BY date) as prev_revenue,
  revenue - LAG(revenue) OVER (ORDER BY date) as change,
  ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY date)) / 
    NULLIF(LAG(revenue) OVER (ORDER BY date), 0), 2) as pct_change
FROM daily_sales;""",
        "explanation": "LAG with calculation for period-over-period comparison"
    },
    {
        "instruction": "Self-join to find related records",
        "sql": """SELECT 
  e.name as employee,
  m.name as manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;""",
        "explanation": "Self-join connects table to itself"
    },
    {
        "instruction": "Cross join for all combinations",
        "sql": """SELECT 
  p.name as product,
  s.name as size,
  c.name as color
FROM products p
CROSS JOIN sizes s
CROSS JOIN colors c;""",
        "explanation": "CROSS JOIN creates Cartesian product"
    },
    {
        "instruction": "Lateral join for per-row subquery",
        "sql": """SELECT 
  c.name,
  recent.order_date,
  recent.total
FROM customers c
LEFT JOIN LATERAL (
  SELECT order_date, total
  FROM orders
  WHERE customer_id = c.id
  ORDER BY order_date DESC
  LIMIT 3
) recent ON true;""",
        "explanation": "LATERAL allows subquery to reference outer table"
    },
    {
        "instruction": "Use CTE for readability",
        "sql": """WITH monthly_sales AS (
  SELECT 
    DATE_TRUNC('month', order_date) as month,
    SUM(total) as revenue
  FROM orders
  GROUP BY DATE_TRUNC('month', order_date)
),
growth AS (
  SELECT 
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) as prev_month
  FROM monthly_sales
)
SELECT 
  month,
  revenue,
  ROUND(100.0 * (revenue - prev_month) / prev_month, 2) as growth_pct
FROM growth;""",
        "explanation": "Multiple CTEs for step-by-step query building"
    },
    {
        "instruction": "Conditional update with CASE",
        "sql": """UPDATE products
SET price = CASE 
  WHEN category = 'Electronics' THEN price * 1.1
  WHEN category = 'Books' THEN price * 1.05
  ELSE price
END
WHERE discount_eligible = true;""",
        "explanation": "CASE in UPDATE for conditional modifications"
    },
    {
        "instruction": "Delete with subquery",
        "sql": """DELETE FROM orders
WHERE customer_id IN (
  SELECT id FROM customers WHERE status = 'deleted'
);""",
        "explanation": "Subquery in WHERE for related deletions"
    },
    {
        "instruction": "Insert from select with transformation",
        "sql": """INSERT INTO archive_orders (id, customer_id, total, archived_at)
SELECT id, customer_id, total, NOW()
FROM orders
WHERE created_at < '2023-01-01' AND status = 'completed';""",
        "explanation": "INSERT SELECT for data archival"
    },
    {
        "instruction": "Merge/upsert multiple rows",
        "sql": """INSERT INTO inventory (product_id, quantity)
SELECT product_id, quantity FROM staging_inventory
ON CONFLICT (product_id) DO UPDATE SET
  quantity = inventory.quantity + EXCLUDED.quantity,
  updated_at = NOW();""",
        "explanation": "Bulk upsert from staging table"
    },
    {
        "instruction": "Generate date series",
        "sql": """SELECT generate_series(
  '2024-01-01'::date,
  '2024-12-31'::date,
  '1 day'::interval
)::date as date;""",
        "explanation": "Generate series for date dimension"
    },
    {
        "instruction": "Fill gaps in time series",
        "sql": """SELECT 
  d.date,
  COALESCE(s.value, 0) as value
FROM generate_series('2024-01-01', '2024-01-31', '1 day'::interval) d(date)
LEFT JOIN sales s ON s.date = d.date::date
ORDER BY d.date;""",
        "explanation": "Join to generated series fills missing dates"
    },
    {
        "instruction": "Query JSON data",
        "sql": """SELECT 
  id,
  data->>'name' as name,
  (data->'address'->>'city') as city,
  (data->'scores'->>0)::int as first_score
FROM users_json;""",
        "explanation": "JSON operators: -> gets JSON, ->> gets text"
    },
    {
        "instruction": "Update JSON field",
        "sql": """UPDATE users_json
SET data = jsonb_set(data, '{address,city}', '"New York"')
WHERE id = 1;""",
        "explanation": "jsonb_set updates nested JSON values"
    },
    {
        "instruction": "Array operations",
        "sql": """SELECT 
  id,
  tags,
  array_length(tags, 1) as tag_count,
  tags[1] as first_tag,
  'featured' = ANY(tags) as is_featured
FROM products;""",
        "explanation": "PostgreSQL array functions and operators"
    },
    {
        "instruction": "Full-text search",
        "sql": """SELECT 
  id,
  title,
  ts_rank(search_vector, query) as rank
FROM posts,
  to_tsquery('english', 'postgresql & performance') query
WHERE search_vector @@ query
ORDER BY rank DESC;""",
        "explanation": "PostgreSQL full-text search with ranking"
    },
    {
        "instruction": "Explain query plan",
        "sql": """EXPLAIN ANALYZE
SELECT o.*, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.created_at > '2024-01-01';""",
        "explanation": "EXPLAIN ANALYZE shows actual execution plan and timing"
    },
    {
        "instruction": "Lock table for update",
        "sql": """SELECT * FROM inventory
WHERE product_id = 123
FOR UPDATE NOWAIT;""",
        "explanation": "FOR UPDATE locks rows for transaction"
    },
    {
        "instruction": "Batch update with limit",
        "sql": """WITH batch AS (
  SELECT id FROM large_table
  WHERE processed = false
  LIMIT 1000
  FOR UPDATE SKIP LOCKED
)
UPDATE large_table
SET processed = true
WHERE id IN (SELECT id FROM batch);""",
        "explanation": "Batch processing with row locking"
    },
]

# =============================================================================
# DATABASE DESIGN
# =============================================================================

DESIGN_TASKS = [
    {
        "instruction": "Design a schema for a blog with users, posts, and comments",
        "sql": """-- Users table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Posts table
CREATE TABLE posts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) UNIQUE NOT NULL,
  content TEXT,
  published BOOLEAN DEFAULT FALSE,
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Comments table
CREATE TABLE comments (
  id SERIAL PRIMARY KEY,
  post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_posts_user ON posts(user_id);
CREATE INDEX idx_posts_slug ON posts(slug);
CREATE INDEX idx_comments_post ON comments(post_id);""",
        "explanation": "Normalized design with foreign keys, cascading deletes, indexes"
    },
    {
        "instruction": "Create index for frequently queried columns",
        "sql": """-- Single column index
CREATE INDEX idx_users_email ON users(email);

-- Composite index (column order matters!)
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- Partial index (only active records)
CREATE INDEX idx_active_users ON users(email) WHERE active = true;

-- Covering index (includes all needed columns)
CREATE INDEX idx_products_search ON products(category_id, name) INCLUDE (price, stock);""",
        "explanation": "Different index types for different query patterns"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Optimize a slow database query",
        "steps": [
            "Get the query execution plan: EXPLAIN ANALYZE <query>",
            "Identify table scans vs index scans",
            "Check for missing indexes on WHERE/JOIN columns",
            "Look for estimated vs actual row mismatches",
            "Check if statistics are up to date: ANALYZE table",
            "Consider index-only scans (covering indexes)",
            "Evaluate query structure (subqueries vs joins)",
            "Test with added indexes",
            "Compare execution times before/after"
        ]
    },
    {
        "instruction": "Set up database replication for high availability",
        "steps": [
            "Identify replication strategy (streaming, logical)",
            "Configure primary server for replication",
            "Set up replication user with appropriate permissions",
            "Take base backup of primary",
            "Restore backup on replica server",
            "Configure replica to connect to primary",
            "Start replication and verify lag",
            "Set up monitoring for replication status",
            "Test failover procedure",
            "Document recovery steps"
        ]
    },
    {
        "instruction": "Migrate database schema without downtime",
        "steps": [
            "Create new columns/tables alongside existing",
            "Deploy code that writes to both old and new",
            "Backfill historical data in batches",
            "Verify data consistency between old and new",
            "Deploy code that reads from new",
            "Remove writes to old schema",
            "Deploy code that only uses new schema",
            "Drop old columns/tables after verification",
            "Update indexes for new query patterns"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is database normalization?",
        "answer": "Normalization organizes data to reduce redundancy and improve integrity. Normal forms: 1NF (atomic values, no repeating groups), 2NF (1NF + no partial dependencies), 3NF (2NF + no transitive dependencies). Benefits: less storage, easier updates, consistent data. Trade-offs: more JOINs needed, can impact read performance. Denormalization intentionally adds redundancy for read performance (common in analytics)."
    },
    {
        "question": "What is a database index?",
        "answer": "An index is a data structure that speeds up queries by allowing quick lookup without scanning entire table. Like a book's index pointing to pages. B-tree indexes are most common (good for ranges and equality). Hash indexes for equality only. Indexes speed up reads but slow writes (must update index too). Over-indexing wastes space and slows inserts. Create indexes on columns in WHERE, JOIN, ORDER BY clauses."
    },
    {
        "question": "What is the difference between INNER JOIN and LEFT JOIN?",
        "answer": "INNER JOIN returns only rows with matches in both tables. LEFT JOIN returns all rows from left table, with NULLs for non-matching right table rows. RIGHT JOIN is opposite. FULL OUTER JOIN returns all rows from both. Use LEFT JOIN to find 'orphan' records (no match in other table). INNER JOIN is default; LEFT JOIN is more common for optional relationships."
    },
    {
        "question": "What are database transactions?",
        "answer": "Transactions group operations into atomic units - all succeed or all fail. ACID properties: Atomicity (all or nothing), Consistency (valid state to valid state), Isolation (concurrent transactions don't interfere), Durability (committed data persists). START TRANSACTION, COMMIT, ROLLBACK. Isolation levels trade consistency for performance: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE."
    },
    # NEW: Additional basic concepts
    {
        "question": "What is a primary key?",
        "answer": "Primary key uniquely identifies each row in a table. Must be unique and NOT NULL. Usually an auto-incrementing integer (SERIAL) or UUID. Composite primary keys use multiple columns. Referenced by foreign keys in other tables. Should be immutable - don't use business data (email, SSN) as PK. Natural keys vs surrogate keys: surrogate (ID) preferred for stability."
    },
    {
        "question": "What is a foreign key?",
        "answer": "Foreign key creates relationship between tables by referencing another table's primary key. Enforces referential integrity - can't insert invalid references. ON DELETE options: CASCADE (delete children), SET NULL, RESTRICT (prevent delete). ON UPDATE works similarly. Foreign keys should be indexed for JOIN performance. Many-to-many relationships use junction/bridge tables with two foreign keys."
    },
    {
        "question": "What is the difference between WHERE and HAVING?",
        "answer": "WHERE filters rows before grouping/aggregation. HAVING filters groups after aggregation. WHERE can't use aggregate functions (SUM, COUNT); HAVING can. Order: FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY. Example: WHERE status='active' filters individual rows; HAVING COUNT(*)>5 filters groups with more than 5 members."
    },
    {
        "question": "What is SQL injection and how do I prevent it?",
        "answer": "SQL injection attacks insert malicious SQL through user input. Example: input ' OR 1=1 -- turns WHERE user='input' into WHERE user='' OR 1=1 --, returning all rows. Prevention: 1) Use parameterized queries/prepared statements (NEVER concatenate user input into SQL), 2) Input validation, 3) Least privilege database accounts, 4) ORM libraries handle it automatically. Always parameterize: cursor.execute('SELECT * FROM users WHERE id=%s', (user_id,))."
    },
    {
        "question": "What is ACID in databases?",
        "answer": "ACID guarantees reliable database transactions: Atomicity - transaction is all-or-nothing, partial completion impossible. Consistency - database moves from one valid state to another. Isolation - concurrent transactions don't interfere with each other. Durability - committed changes survive crashes. NoSQL databases often sacrifice some ACID for performance (BASE: Basically Available, Soft state, Eventually consistent)."
    },
    {
        "question": "What is a database view?",
        "answer": "A view is a stored query that acts like a virtual table. Created with CREATE VIEW name AS SELECT... Views simplify complex queries, provide security by limiting visible columns, and present consistent interface even if underlying tables change. Materialized views store results physically for faster access but need refreshing. Regular views are computed on each access."
    },
    {
        "question": "What is the difference between DELETE, TRUNCATE, and DROP?",
        "answer": "DELETE removes specific rows (can have WHERE), logs each deletion, can be rolled back, triggers fire. TRUNCATE removes ALL rows, faster than DELETE, can be rolled back in some databases, resets auto-increment. DROP removes the entire table structure and data, schema change. Use DELETE for selective removal, TRUNCATE for clearing tables, DROP to remove table entirely."
    },
    {
        "question": "What is a stored procedure?",
        "answer": "Stored procedure is precompiled SQL code stored in the database. Benefits: reduced network traffic (one call vs many), better security (grant execute without table access), reusable business logic, compiled execution plan. Drawbacks: harder to version control, vendor-specific syntax, can hide logic from application developers. Good for: complex multi-step operations, data validation, batch processing."
    },
    {
        "question": "What is a database trigger?",
        "answer": "Trigger is code that automatically executes before/after INSERT, UPDATE, DELETE. Use cases: auditing (log changes), enforcing business rules, maintaining derived data, syncing related tables. Triggers can be tricky: hidden logic, performance impact, debugging difficulty. Use sparingly - business logic often better in application. BEFORE triggers can modify data, AFTER triggers see final values."
    },
    {
        "question": "How do I paginate query results?",
        "answer": "Basic pagination: LIMIT rows OFFSET skip. Page 3 with 20 per page: LIMIT 20 OFFSET 40. Problem: OFFSET scans and discards rows, slow for large offsets. Better: keyset/cursor pagination - remember last seen value: WHERE id > last_id LIMIT 20. Requires consistent ordering. For total count: separate COUNT(*) query or window function COUNT(*) OVER()."
    },
    {
        "question": "What is NULL in SQL?",
        "answer": "NULL represents missing/unknown value, not zero or empty string. NULL != NULL (use IS NULL, IS NOT NULL). NULL in comparisons yields NULL (not true/false). COALESCE(col, default) returns first non-NULL. NULLIF(a, b) returns NULL if a=b. NULLs sort differently by database. COUNT(*) counts NULLs, COUNT(column) doesn't. Be explicit about NULL handling in your queries."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "What are window functions?",
        "answer": "Window functions perform calculations across rows related to current row without collapsing into single output. Unlike GROUP BY, they keep all rows. Syntax: function() OVER (PARTITION BY ... ORDER BY ...). Common functions: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(), SUM(), AVG(). Use for running totals, rankings, comparing to previous row. Very powerful for analytics queries."
    },
    {
        "question": "How do database locks work?",
        "answer": "Locks prevent concurrent modification conflicts. Types: shared (read) locks allow multiple readers, exclusive (write) locks block everyone else. Granularity: row-level (fine, more overhead), table-level (coarse, less concurrency). Lock escalation happens when too many row locks. Deadlocks occur when transactions wait for each other - database detects and kills one. MVCC (PostgreSQL) uses snapshots instead of locking for reads."
    },
    {
        "question": "What is query plan optimization?",
        "answer": "The query optimizer chooses how to execute SQL. Steps: parse SQL, generate possible plans, estimate costs, choose cheapest. Costs based on: row estimates, I/O, CPU. EXPLAIN shows the plan. Common operations: Seq Scan (full table), Index Scan, Hash Join, Nested Loop, Sort. Statistics (pg_stats) inform estimates - run ANALYZE to update. Bad estimates lead to bad plans. Indexes, query structure, and statistics all affect optimization."
    },
    {
        "question": "How does database sharding work?",
        "answer": "Sharding horizontally partitions data across multiple databases. Each shard holds subset of data (e.g., users A-M on shard1, N-Z on shard2). Benefits: horizontal scaling, more write capacity. Challenges: cross-shard queries are hard, maintaining consistency, resharding is painful. Shard key selection is critical - must be in most queries. Alternatives: read replicas for read scaling, vertical scaling first. Consider only when truly needed."
    },
    # NEW: Additional advanced concepts
    {
        "question": "What is database replication?",
        "answer": "Replication copies data across multiple database servers. Types: synchronous (waits for replica confirmation, stronger consistency) vs asynchronous (faster, eventual consistency). Master-slave: writes to master, reads from replicas. Multi-master: writes anywhere, conflict resolution needed. Streaming replication sends WAL continuously. Logical replication is table-level, selective. Use for: high availability, read scaling, backups, geographic distribution."
    },
    {
        "question": "What is a CTE (Common Table Expression)?",
        "answer": "CTE is a named temporary result set defined with WITH clause. Improves readability by breaking complex queries into logical steps. WITH cte AS (SELECT...) SELECT * FROM cte. Can be referenced multiple times in main query. Recursive CTEs (WITH RECURSIVE) traverse hierarchies and graphs. Some databases materialize CTEs (PostgreSQL pre-12), others inline them. Great for: complex joins, step-by-step transformations, self-referencing data."
    },
    {
        "question": "What is MVCC (Multi-Version Concurrency Control)?",
        "answer": "MVCC allows concurrent transactions to see consistent snapshots without blocking each other. Each transaction sees database as of its start time. Writes create new versions rather than overwriting. Old versions kept for active transactions. PostgreSQL uses xmin/xmax for versioning. Benefits: readers don't block writers, writers don't block readers. Costs: bloat from old versions (VACUUM cleans up), transaction ID wraparound management."
    },
    {
        "question": "What are isolation levels and when should I use each?",
        "answer": "READ UNCOMMITTED: sees uncommitted changes (dirty reads), rarely used. READ COMMITTED (PostgreSQL default): sees only committed data, may see changes mid-transaction. REPEATABLE READ: consistent snapshot, prevents phantom reads in PostgreSQL. SERIALIZABLE: transactions appear sequential, prevents all anomalies but may abort. Higher isolation = more consistency, less concurrency. Use READ COMMITTED for most apps, SERIALIZABLE for financial/critical transactions."
    },
    {
        "question": "What is database partitioning?",
        "answer": "Partitioning divides large tables into smaller pieces. Types: Range (date ranges), List (specific values), Hash (distribute evenly). Benefits: query only relevant partitions, easier maintenance (drop old partitions), parallel query execution. PostgreSQL: declarative partitioning with PARTITION BY. Common pattern: time-series data partitioned by month/year. Different from sharding: partitions are within one database, shards are separate servers."
    },
    {
        "question": "How do I design for high write throughput?",
        "answer": "Strategies: 1) Batch inserts (multi-row INSERT), 2) Reduce indexes on write-heavy tables, 3) Use COPY for bulk loads, 4) Disable triggers during bulk operations, 5) Async writes with message queue, 6) Connection pooling (PgBouncer), 7) Partition tables, 8) Use appropriate isolation level, 9) Consider columnar storage for analytics, 10) Scale horizontally with sharding. Profile to find bottleneck: I/O, CPU, locks, or network."
    },
    {
        "question": "What is connection pooling?",
        "answer": "Connection pooling reuses database connections instead of creating new ones per request. Creating connections is expensive (authentication, TLS, process spawning). Poolers: PgBouncer (PostgreSQL), ProxySQL (MySQL), application-level pools. Pool modes: session (one client per connection), transaction (reuse after transaction), statement (reuse after each query). Size pool based on: database max_connections, typical concurrent queries, server resources."
    },
    {
        "question": "What is a database migration?",
        "answer": "Migration is versioned schema change applied to database. Tools: Flyway, Liquibase, Alembic, Django migrations. Each migration has up (apply) and down (rollback) scripts. Track applied migrations in database table. Run in order, never skip. Best practices: small incremental changes, test rollbacks, handle data carefully, avoid locking during migrations. Expand-contract pattern: add new, migrate data, remove old - for zero downtime."
    },
    {
        "question": "How do I handle time zones in databases?",
        "answer": "Best practice: store all timestamps in UTC (TIMESTAMP WITH TIME ZONE in PostgreSQL). Convert to local time in application/display layer. Never use TIMESTAMP WITHOUT TIME ZONE for anything that matters. Set timezone at session level when needed. Store user's timezone preference separately. For date-only, consider if date is 'user's local date' or 'UTC date'. Be explicit: created_at vs user_local_date. Watch for daylight saving time edge cases."
    },
    {
        "question": "What is the N+1 query problem?",
        "answer": "N+1 occurs when code fetches list of N items, then makes N additional queries for related data. Example: get 100 orders, then 100 separate queries for customer info. Fix with JOINs: SELECT orders.*, customers.* FROM orders JOIN customers..., or batch loading: WHERE customer_id IN (...). ORMs often cause this - use eager loading (Django: select_related, SQLAlchemy: joinedload). Monitor query count in development."
    },
    {
        "question": "What is a covering index?",
        "answer": "Covering index includes all columns needed by a query, avoiding table access entirely. PostgreSQL INCLUDE clause: CREATE INDEX idx ON orders(customer_id) INCLUDE (total, status). Index-only scan reads index without touching heap. Trade-off: larger index size, more write overhead. Great for: frequently-run queries with specific column sets, read-heavy workloads. Check EXPLAIN for 'Index Only Scan' to verify effectiveness."
    },
    {
        "question": "What is database denormalization?",
        "answer": "Denormalization intentionally adds redundancy for read performance. Examples: store calculated totals, duplicate data from related tables, pre-joined data. Benefits: fewer JOINs, faster reads. Costs: data inconsistency risk, more storage, slower writes (must update copies). Use when: read-heavy workloads, analytics, caching aggregates. Maintain consistency with: triggers, application logic, eventual consistency patterns, materialized views."
    },
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "DELETE FROM users (no WHERE clause)",
        "error_type": "dangerous_operation",
        "response": {
            "status": "blocked",
            "severity": "critical",
            "message": "STOP - This deletes ALL users!",
            "explanation": "DELETE without WHERE removes every row in the table",
            "safe_approach": [
                "Always include WHERE clause",
                "Test with SELECT first: SELECT * FROM users WHERE <condition>",
                "Use LIMIT for safety: DELETE FROM users WHERE id = 1 LIMIT 1",
                "Consider soft deletes: UPDATE users SET deleted_at = NOW() WHERE..."
            ]
        }
    },
    {
        "instruction": "Query is running for hours",
        "error_type": "performance",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check EXPLAIN ANALYZE output",
                "Look for sequential scans on large tables",
                "Check for missing indexes on JOIN/WHERE columns",
                "Verify table statistics are current",
                "Look for lock contention: pg_locks, pg_stat_activity"
            ],
            "common_fixes": [
                "Add appropriate indexes",
                "Rewrite subqueries as JOINs",
                "Add LIMIT for large result sets",
                "Use pagination instead of fetching all",
                "ANALYZE tables to update statistics"
            ]
        }
    },
    {
        "instruction": "Deadlock detected error",
        "error_type": "concurrency",
        "response": {
            "status": "recoverable",
            "explanation": "Two transactions are waiting for each other's locks",
            "immediate_fix": "Retry the transaction - database already rolled one back",
            "prevention": [
                "Access tables in consistent order across transactions",
                "Keep transactions short",
                "Use SELECT FOR UPDATE to lock early",
                "Consider SERIALIZABLE isolation level"
            ]
        }
    },
    {
        "instruction": "Foreign key constraint violation",
        "error_type": "constraint_error",
        "response": {
            "status": "data_integrity",
            "explanation": "Trying to insert/delete data that violates referential integrity",
            "common_causes": [
                "Inserting with non-existent parent ID",
                "Deleting parent that has child records",
                "Data wasn't migrated in correct order"
            ],
            "solutions": [
                "Insert parent record first, then children",
                "Delete children first, then parent",
                "Use ON DELETE CASCADE if appropriate",
                "Check and fix orphan records"
            ]
        }
    },
    {
        "instruction": "Database connection refused error",
        "error_type": "connectivity",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Is database server running?",
                "Check host and port in connection string",
                "Verify network connectivity (firewall, security groups)",
                "Check pg_hba.conf for allowed connections",
                "Verify max_connections not exceeded"
            ],
            "common_fixes": [
                "Start database service",
                "Use correct hostname (localhost vs IP)",
                "Add IP to allowed hosts in pg_hba.conf",
                "Increase max_connections if at limit"
            ]
        }
    },
    {
        "instruction": "Out of disk space error",
        "error_type": "resource_exhaustion",
        "response": {
            "status": "critical",
            "immediate_actions": [
                "Check disk usage: df -h",
                "Identify large tables: SELECT pg_size_pretty(pg_database_size('dbname'))",
                "Check for bloat: pg_stat_user_tables",
                "Review WAL files accumulation"
            ],
            "solutions": [
                "VACUUM FULL to reclaim space (locks table)",
                "Delete old data or archive to cold storage",
                "Increase disk size",
                "Configure log rotation",
                "Review WAL retention settings"
            ]
        }
    },
    {
        "instruction": "Unique constraint violation",
        "error_type": "constraint_error",
        "response": {
            "status": "data_error",
            "explanation": "Trying to insert duplicate value in unique column",
            "solutions": [
                "Check if record already exists before insert",
                "Use ON CONFLICT (col) DO UPDATE for upserts",
                "Use ON CONFLICT DO NOTHING to skip duplicates",
                "Review if uniqueness constraint is correct"
            ],
            "code_example": "INSERT INTO users (email, name) VALUES ($1, $2) ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name"
        }
    },
    {
        "instruction": "Database migration failed",
        "error_type": "schema_error",
        "response": {
            "status": "needs_resolution",
            "steps": [
                "Check migration logs for specific error",
                "Verify database connection and permissions",
                "Check for incompatible data (e.g., adding NOT NULL to column with NULLs)",
                "Review migration script for syntax errors"
            ],
            "recovery": [
                "Fix the issue and retry migration",
                "Rollback if possible: migration tool rollback command",
                "If stuck, manually fix database state",
                "Mark migration as applied if manually resolved"
            ]
        }
    },
    {
        "instruction": "Query returning wrong results",
        "error_type": "logic_error",
        "response": {
            "status": "debug",
            "diagnostic_approach": [
                "Break query into parts and test each",
                "Check JOIN conditions - wrong columns?",
                "Verify WHERE conditions are correct",
                "Check for implicit type conversions",
                "Look for NULL handling issues"
            ],
            "common_causes": [
                "Wrong JOIN type (INNER vs LEFT)",
                "Missing JOIN condition causing cartesian product",
                "WHERE condition on wrong table",
                "NULL comparisons (use IS NULL, not = NULL)"
            ]
        }
    },
    {
        "instruction": "DROP TABLE production_data",
        "error_type": "dangerous_operation",
        "response": {
            "status": "blocked",
            "severity": "critical",
            "reason": "DROP TABLE permanently removes table and all data",
            "verification_required": [
                "Confirm this is not production database",
                "Verify backup exists and is recent",
                "Understand that this cannot be undone",
                "Consider TRUNCATE if only deleting data"
            ],
            "if_intentional": "First backup: pg_dump -t production_data dbname > backup.sql"
        }
    },
    {
        "instruction": "Too many database connections error",
        "error_type": "resource_limit",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "Check active connections: SELECT count(*) FROM pg_stat_activity",
            "immediate_fixes": [
                "Terminate idle connections",
                "Restart application with connection leaks",
                "Increase max_connections (requires restart)"
            ],
            "long_term_solutions": [
                "Use connection pooler (PgBouncer)",
                "Fix connection leaks in application",
                "Reduce connection pool size per app instance",
                "Use fewer long-lived connections"
            ]
        }
    },
    {
        "instruction": "Data type mismatch error",
        "error_type": "type_error",
        "response": {
            "status": "fixable",
            "cause": "Column type doesn't match provided value",
            "solutions": [
                "Cast value explicitly: CAST(value AS integer)",
                "Check column type: \\d tablename in psql",
                "Fix application code sending wrong type",
                "Use type-safe parameterized queries"
            ],
            "prevention": "Use ORM with type checking or validate before query"
        }
    },
    {
        "instruction": "Table locked, query waiting",
        "error_type": "concurrency",
        "response": {
            "status": "investigate",
            "diagnosis_queries": [
                "SELECT * FROM pg_locks WHERE NOT granted;",
                "SELECT * FROM pg_stat_activity WHERE wait_event_type IS NOT NULL;",
                "Check for long-running transactions"
            ],
            "solutions": [
                "Wait for blocking transaction to complete",
                "Cancel blocking query: SELECT pg_cancel_backend(pid)",
                "In emergency: SELECT pg_terminate_backend(pid)",
                "Review application for long transactions"
            ],
            "prevention": "Keep transactions short, avoid DDL during peak"
        }
    },
    {
        "instruction": "Index not being used by query",
        "error_type": "performance",
        "response": {
            "status": "optimize",
            "diagnosis": "Run EXPLAIN ANALYZE to see actual plan",
            "reasons_index_ignored": [
                "Query returns too many rows (full scan cheaper)",
                "Statistics outdated - run ANALYZE",
                "Using function on column: WHERE LOWER(name) needs functional index",
                "Type mismatch between column and value",
                "Index doesn't match query pattern"
            ],
            "solutions": [
                "Run ANALYZE on table",
                "Create covering index for specific query",
                "Create functional index if using functions",
                "Check column order in composite index"
            ]
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_sql_response(sql: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_sql",
        "sql": sql,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    examples = []
    for task in BASIC_SQL_TASKS + ADVANCED_SQL_TASKS + DESIGN_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_sql_response(task["sql"], task["explanation"])
        })
    return examples

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in BASIC_CONCEPTS + ADVANCED_CONCEPTS]

def generate_error_examples() -> List[Dict]:
    examples = []
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    return examples

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Database Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} SQL examples")
    
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"Generated {len(planning_examples)} planning examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "database_sql.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
