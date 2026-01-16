# Simple RDBMS

A lightweight relational database management system with SQL interface.

## Features

- **Data Types**: INTEGER, TEXT, REAL, BOOLEAN
- **Constraints**: PRIMARY KEY, UNIQUE, NOT NULL
- **CRUD Operations**: CREATE TABLE, DROP TABLE, INSERT, SELECT, UPDATE, DELETE
- **JOINs**: INNER JOIN, LEFT JOIN, RIGHT JOIN, CROSS JOIN
- **Indexing**: B-tree indexes on PRIMARY KEY and UNIQUE columns
- **Interactive REPL**: Command history, multi-line input, meta-commands

## Quick Start

```bash
# Start interactive REPL
python3 main.py

# Execute single command
python3 main.py -c "SELECT 1 + 1;"

# Execute from file
python3 main.py -f script.sql
```

## Usage Examples

```sql
-- Create a table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    active BOOLEAN
);

-- Insert data
INSERT INTO users (id, name, email, active) VALUES
    (1, 'Alice', 'alice@example.com', true),
    (2, 'Bob', 'bob@example.com', true),
    (3, 'Charlie', 'charlie@example.com', false);

-- Query data
SELECT * FROM users WHERE active = true;
SELECT name, email FROM users ORDER BY name ASC;

-- Join tables
SELECT u.name, o.total 
FROM users u 
INNER JOIN orders o ON u.id = o.user_id
WHERE o.total > 100;

-- Update data
UPDATE users SET active = false WHERE id = 2;

-- Delete data
DELETE FROM users WHERE active = false;
```

## Meta-Commands

| Command | Description |
|---------|-------------|
| `.tables` | List all tables |
| `.schema [table]` | Show table schema |
| `.indexes [table]` | Show indexes |
| `.clear` | Clear the database |
| `.help` | Show help |
| `.quit` | Exit REPL |

## SQL Reference

### Data Types

| Type | Aliases | Description |
|------|---------|-------------|
| `INTEGER` | `INT` | 64-bit signed integer |
| `TEXT` | `VARCHAR`, `STRING` | Variable-length string |
| `REAL` | `FLOAT`, `DOUBLE` | Floating-point number |
| `BOOLEAN` | `BOOL` | Boolean (true/false) |

### Constraints

- `PRIMARY KEY` - Unique, non-null identifier (auto-indexed)
- `UNIQUE` - Must be unique (allows NULL, auto-indexed)
- `NOT NULL` - Cannot be NULL

### Operators

| Operator | Description |
|----------|-------------|
| `=`, `<>` | Equality, inequality |
| `<`, `<=`, `>`, `>=` | Comparison |
| `AND`, `OR`, `NOT` | Logical |
| `IS NULL`, `IS NOT NULL` | NULL checks |
| `LIKE` | Pattern matching (`%` = any, `_` = single char) |

## Architecture

```
main.py          # Entry point with REPL
├── lexer.py     # SQL tokenization
├── parser.py    # SQL parsing to AST
├── ast_nodes.py # AST node definitions
├── executor.py  # Query execution
├── storage.py   # Table and row storage
├── index.py     # B-tree indexing
├── schema.py    # Schema management
├── datatypes.py # Data type handling
└── exceptions.py # Error types
```

## License

MIT
