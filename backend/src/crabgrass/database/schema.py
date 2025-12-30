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

-- =============================================================================
-- V2 TABLES
-- =============================================================================

-- Objectives table
CREATE TABLE IF NOT EXISTS objectives (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Retired')),
    author_id VARCHAR NOT NULL,
    parent_id VARCHAR,
    embedding FLOAT[768],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    message TEXT NOT NULL,
    source_type VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    related_id VARCHAR,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Queue items table (async processing)
CREATE TABLE IF NOT EXISTS queue_items (
    id VARCHAR PRIMARY KEY,
    queue VARCHAR NOT NULL,
    payload JSON NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Relationships table (agent-discovered connections)
CREATE TABLE IF NOT EXISTS relationships (
    id VARCHAR PRIMARY KEY,
    from_type VARCHAR NOT NULL,
    from_id VARCHAR NOT NULL,
    to_type VARCHAR NOT NULL,
    to_id VARCHAR NOT NULL,
    relationship VARCHAR NOT NULL,
    score FLOAT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    discovered_by VARCHAR
);

-- Watches table (users watching ideas/objectives)
CREATE TABLE IF NOT EXISTS watches (
    user_id VARCHAR NOT NULL,
    target_type VARCHAR NOT NULL,
    target_id VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, target_type, target_id)
);

-- Idea-Objective links table
CREATE TABLE IF NOT EXISTS idea_objectives (
    idea_id VARCHAR NOT NULL,
    objective_id VARCHAR NOT NULL,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (idea_id, objective_id)
);

-- =============================================================================
-- GRAPH EDGE TABLES (for property graph queries)
-- =============================================================================

-- Similarity edges (populated by batch job from ConnectionAgent discoveries)
CREATE TABLE IF NOT EXISTS graph_similar_ideas (
    from_idea_id VARCHAR NOT NULL,
    to_idea_id VARCHAR NOT NULL,
    similarity_score FLOAT NOT NULL,
    match_type VARCHAR NOT NULL,  -- 'summary', 'challenge', 'approach'
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_idea_id, to_idea_id, match_type)
);

CREATE TABLE IF NOT EXISTS graph_similar_challenges (
    from_challenge_id VARCHAR NOT NULL,
    to_challenge_id VARCHAR NOT NULL,
    similarity_score FLOAT NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_challenge_id, to_challenge_id)
);

CREATE TABLE IF NOT EXISTS graph_similar_approaches (
    from_approach_id VARCHAR NOT NULL,
    to_approach_id VARCHAR NOT NULL,
    similarity_score FLOAT NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_approach_id, to_approach_id)
);

-- Objective hierarchy edges (materialized from parent_id for graph traversal)
CREATE TABLE IF NOT EXISTS graph_objective_hierarchy (
    parent_id VARCHAR NOT NULL,
    child_id VARCHAR NOT NULL,
    depth INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (parent_id, child_id)
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

-- V2 Indexes

-- Queue processing index (find pending items quickly)
CREATE INDEX IF NOT EXISTS idx_queue_items_pending
ON queue_items (queue, status, created_at)
WHERE status = 'pending';

-- Notifications index (user's unread notifications)
CREATE INDEX IF NOT EXISTS idx_notifications_user
ON notifications (user_id, read, created_at DESC);

-- Relationships indexes (lookup by from/to)
CREATE INDEX IF NOT EXISTS idx_relationships_from
ON relationships (from_type, from_id);

CREATE INDEX IF NOT EXISTS idx_relationships_to
ON relationships (to_type, to_id);

-- Objectives embedding index (for similarity search)
CREATE INDEX IF NOT EXISTS objectives_embedding_idx
ON objectives USING HNSW (embedding)
WITH (metric = 'cosine');

-- Graph edge indexes (for efficient traversal)
CREATE INDEX IF NOT EXISTS idx_graph_similar_ideas_from
ON graph_similar_ideas (from_idea_id);

CREATE INDEX IF NOT EXISTS idx_graph_similar_ideas_to
ON graph_similar_ideas (to_idea_id);

CREATE INDEX IF NOT EXISTS idx_graph_similar_challenges_from
ON graph_similar_challenges (from_challenge_id);

CREATE INDEX IF NOT EXISTS idx_graph_similar_approaches_from
ON graph_similar_approaches (from_approach_id);

CREATE INDEX IF NOT EXISTS idx_graph_objective_hierarchy_parent
ON graph_objective_hierarchy (parent_id);

CREATE INDEX IF NOT EXISTS idx_graph_objective_hierarchy_child
ON graph_objective_hierarchy (child_id);
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
        # Graph edge tables (drop first)
        "graph_similar_ideas",
        "graph_similar_challenges",
        "graph_similar_approaches",
        "graph_objective_hierarchy",
        # V2 tables (drop first due to potential references)
        "idea_objectives",
        "watches",
        "relationships",
        "queue_items",
        "notifications",
        "objectives",
        # V1 tables
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
