"""Read-only data-quality checks for the application database."""

from __future__ import annotations

import argparse
from collections.abc import Iterable

from src.database.connection import get_connection


CHECKS: list[tuple[str, str]] = [
    (
        "songs",
        "SELECT COUNT(*) FROM songs",
    ),
    (
        "role credits",
        "SELECT COUNT(*) FROM song_artists",
    ),
    (
        "general credited artists",
        "SELECT COUNT(*) FROM song_credited_artists",
    ),
    (
        "verified credits",
        "SELECT COUNT(*) FROM verified_song_credits",
    ),
    (
        "source records",
        "SELECT COUNT(*) FROM song_sources",
    ),
    (
        "songs without source records",
        """
        SELECT COUNT(*)
        FROM songs s
        WHERE NOT EXISTS (
            SELECT 1 FROM song_sources ss WHERE ss.song_id = s.song_id
        )
        """,
    ),
    (
        "duplicate song titles within a film",
        """
        SELECT COUNT(*)
        FROM (
            SELECT film_id, LOWER(TRIM(title))
            FROM songs
            GROUP BY film_id, LOWER(TRIM(title))
            HAVING COUNT(*) > 1
        ) duplicates
        """,
    ),
    (
        "orphan artists",
        """
        SELECT COUNT(*)
        FROM artists a
        WHERE NOT EXISTS (
            SELECT 1 FROM song_artists sa WHERE sa.artist_id = a.artist_id
        )
        AND NOT EXISTS (
            SELECT 1
            FROM song_credited_artists sca
            WHERE sca.artist_id = a.artist_id
        )
        AND NOT EXISTS (
            SELECT 1
            FROM verified_song_credits vsc
            WHERE vsc.artist_id = a.artist_id
        )
        """,
    ),
]


def run_checks(database_name: str | None = None) -> list[tuple[str, int]]:
    with get_connection(dbname=database_name) as connection:
        with connection.cursor() as cursor:
            results = []
            for label, query in CHECKS:
                cursor.execute(query)
                results.append((label, int(cursor.fetchone()[0])))
            return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run read-only data-quality checks.")
    parser.add_argument("--database", help="Database name; defaults to DB_NAME.")
    args = parser.parse_args()

    results = run_checks(args.database)
    print("South Indian Music — data validation")
    print("=" * 50)
    for label, value in results:
        status = "OK" if value == 0 or label in {
            "songs",
            "role credits",
            "general credited artists",
            "verified credits",
            "source records",
        } else "CHECK"
        print(f"{status:5} {label}: {value}")


if __name__ == "__main__":
    main()
