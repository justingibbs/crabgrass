"""DuckDB database connection management."""

from pathlib import Path
from contextlib import contextmanager
from typing import Generator

import duckdb

from crabgrass.config import get_settings


# Module-level connection for reuse
_connection: duckdb.DuckDBPyConnection | None = None


def get_db_path() -> Path:
    """Get the database file path, ensuring parent directory exists."""
    settings = get_settings()
    db_path = settings.database_path

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return db_path


def get_connection() -> duckdb.DuckDBPyConnection:
    """Get a persistent database connection (singleton).

    Returns a connection that stays open for the lifetime of the app.
    Use this for read operations and when you need the connection to persist.
    """
    global _connection

    if _connection is None:
        db_path = get_db_path()
        _connection = duckdb.connect(str(db_path))
        _install_extensions(_connection)

    return _connection


def _install_extensions(conn: duckdb.DuckDBPyConnection) -> None:
    """Install and load required DuckDB extensions."""
    # VSS extension for vector similarity search
    conn.execute("INSTALL vss")
    conn.execute("LOAD vss")


@contextmanager
def get_cursor() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Get a cursor for database operations.

    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM ideas")
            results = cursor.fetchall()
    """
    conn = get_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()


def close_connection() -> None:
    """Close the database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


def execute(query: str, parameters: list | None = None) -> duckdb.DuckDBPyConnection:
    """Execute a query and return the connection for chaining.

    Args:
        query: SQL query to execute
        parameters: Optional list of parameters for parameterized queries

    Returns:
        The connection (for .fetchall(), .fetchone(), etc.)
    """
    conn = get_connection()
    if parameters:
        return conn.execute(query, parameters)
    return conn.execute(query)


def fetchall(query: str, parameters: list | None = None) -> list:
    """Execute a query and fetch all results.

    Args:
        query: SQL query to execute
        parameters: Optional list of parameters

    Returns:
        List of result tuples
    """
    return execute(query, parameters).fetchall()


def fetchone(query: str, parameters: list | None = None):
    """Execute a query and fetch one result.

    Args:
        query: SQL query to execute
        parameters: Optional list of parameters

    Returns:
        Single result tuple or None
    """
    return execute(query, parameters).fetchone()
