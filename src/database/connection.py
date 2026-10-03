"""PostgreSQL connection helper."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def get_connection(dbname: str | None = None):
    """Open a PostgreSQL connection using the environment configuration."""
    try:
        import psycopg2
    except ImportError as exc:  # pragma: no cover - dependency is runtime-only
        raise RuntimeError(
            "psycopg2-binary is required for database operations. "
            "Install requirements.txt first."
        ) from exc

    database = dbname or os.getenv("DB_NAME")
    if not database:
        raise ValueError("Database name is not configured.")

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=database,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
