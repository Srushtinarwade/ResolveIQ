import os
from functools import lru_cache

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool


@lru_cache(maxsize=1)
def _get_connection_pool():
    db_uri = os.getenv("DATABASE_URL")

    if not db_uri:
        raise RuntimeError("DATABASE_URL is missing")
    
    if db_uri.startswith("postgresql+psycopg://"):
        db_uri = db_uri.replace("postgresql+psycopg://", "postgresql://", 1)

    return ConnectionPool(
        conninfo=db_uri,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )

@lru_cache(maxsize=1)
def get_checkpointer():
    pool = _get_connection_pool()
    return PostgresSaver(pool)