from typing import Generator
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from app.config import get_settings

# Global connection pool reference, initialized and terminated in FastAPI lifespan
pool: ConnectionPool | None = None


def init_db_pool() -> ConnectionPool:
    """
    Initializes the psycopg synchronous connection pool.
    Configures dict_row so query results map naturally to Python dictionaries.
    """
    global pool
    settings = get_settings()
    pool = ConnectionPool(
        conninfo=settings.DATABASE_URL,
        min_size=settings.DB_POOL_MIN_SIZE,
        max_size=settings.DB_POOL_MAX_SIZE,
        kwargs={"row_factory": dict_row},
        open=True,
    )
    return pool


def close_db_pool() -> None:
    """
    Closes all active and idle database connections in the pool cleanly.
    """
    global pool
    if pool is not None:
        pool.close()
        pool = None


def get_db_connection() -> Generator:
    """
    FastAPI dependency that acquires a connection from the pool for a request
    and releases it back to the pool when the request finishes.
    Transactions are handled cleanly using the connection context manager.
    """
    global pool
    if pool is None:
        raise RuntimeError("Database connection pool is not initialized.")

    with pool.connection() as conn:
        yield conn
