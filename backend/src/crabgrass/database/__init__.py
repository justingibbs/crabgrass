"""Database module - DuckDB connection and schema management."""

from crabgrass.database.connection import (
    get_connection,
    get_cursor,
    close_connection,
    execute,
    fetchall,
    fetchone,
)
from crabgrass.database.schema import (
    init_schema,
    create_indexes,
    reset_database,
)

__all__ = [
    "get_connection",
    "get_cursor",
    "close_connection",
    "execute",
    "fetchall",
    "fetchone",
    "init_schema",
    "create_indexes",
    "reset_database",
]
