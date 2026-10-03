"""Apply the canonical schema to a configured PostgreSQL database."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.database.connection import get_connection

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
MIGRATION_PATH = ROOT / "sql" / "migrations" / "001_provenance_tables.sql"


def apply_sql(database_name: str | None, sql_text: str) -> None:
    connection = get_connection(dbname=database_name)
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_text)
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize or update the South Indian Music database."
    )
    parser.add_argument(
        "--database",
        help="Explicit PostgreSQL database name. Defaults to DB_NAME.",
    )
    parser.add_argument(
        "--migration-only",
        action="store_true",
        help="Apply only the existing-database provenance migration.",
    )
    args = parser.parse_args()

    path = MIGRATION_PATH if args.migration_only else SCHEMA_PATH
    print(f"Applying {path.name}...")
    apply_sql(args.database, path.read_text(encoding="utf-8"))
    print("Database schema update completed.")


if __name__ == "__main__":
    main()
