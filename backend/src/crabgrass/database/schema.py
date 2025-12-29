"""Database schema definitions and initialization."""

from crabgrass.database.connection import get_connection


# SQL statements for creating tables
# Note: DuckDB doesn't support CASCADE/SET NULL in foreign keys, so we omit those
SCHEMA_SQL = """
-- Users table (mock users for demo)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('Frontline', 'Senior')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ideas table
CREATE TABLE IF NOT EXISTS ideas (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Active', 'Archived')),
    author_id VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Summaries table (one per Idea)
CREATE TABLE IF NOT EXISTS summaries (
    id VARCHAR PRIMARY KEY,
    idea_id VARCHAR NOT NULL UNIQUE,
    content TEXT NOT NULL,
    embedding FLOAT[768],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Challenges table
CREATE TABLE IF NOT EXISTS challenges (
    id VARCHAR PRIMARY KEY,
    idea_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    embedding FLOAT[768],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Approaches table
CREATE TABLE IF NOT EXISTS approaches (
    id VARCHAR PRIMARY KEY,
    idea_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    embedding FLOAT[768],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coherent Actions table
CREATE TABLE IF NOT EXISTS coherent_actions (
    id VARCHAR PRIMARY KEY,
    idea_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'In Progress', 'Complete')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table (agent conversations)
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    idea_id VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Archived')),
    messages JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# SQL for creating vector similarity indexes
INDEX_SQL = """
-- Create HNSW indexes for vector similarity search
-- Note: These are created after data is inserted for better performance

CREATE INDEX IF NOT EXISTS summaries_embedding_idx
ON summaries USING HNSW (embedding)
WITH (metric = 'cosine');

CREATE INDEX IF NOT EXISTS challenges_embedding_idx
ON challenges USING HNSW (embedding)
WITH (metric = 'cosine');

CREATE INDEX IF NOT EXISTS approaches_embedding_idx
ON approaches USING HNSW (embedding)
WITH (metric = 'cosine');
"""


def init_schema() -> None:
    """Initialize the database schema.

    Creates all tables if they don't exist.
    Call this once at application startup.
    """
    conn = get_connection()

    # Execute each statement separately
    for statement in SCHEMA_SQL.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(statement)

    conn.commit()


def create_indexes() -> None:
    """Create vector similarity indexes.

    Call this after initial data is loaded for better index performance.
    """
    conn = get_connection()

    for statement in INDEX_SQL.split(";"):
        statement = statement.strip()
        if statement:
            try:
                conn.execute(statement)
            except Exception as e:
                # Index might already exist or table might be empty
                print(f"Note: Could not create index: {e}")

    conn.commit()


def drop_all_tables() -> None:
    """Drop all tables. Use with caution - for testing only."""
    conn = get_connection()

    tables = [
        "sessions",
        "coherent_actions",
        "approaches",
        "challenges",
        "summaries",
        "ideas",
        "users",
    ]

    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    conn.commit()


def reset_database() -> None:
    """Reset the database to a clean state. For testing only."""
    drop_all_tables()
    init_schema()
