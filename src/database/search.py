"""Read-only search and detail queries for the music database."""

from __future__ import annotations

from dataclasses import dataclass

from src.database.connection import get_connection


@dataclass
class SongSearchResult:
    song_id: int
    title: str
    film: str
    release_year: int | None
    language: str


@dataclass
class SongDetails:
    song_id: int
    title: str
    film: str
    release_year: int | None
    language: str
    credited_artists: list[str]
    singers: list[str]
    composers: list[str]
    lyricists: list[str]
    verified_singers: list[str]
    verified_composers: list[str]
    verified_lyricists: list[str]
    sources: list[dict]
    credited_artist_sources: list[dict]
    verified_sources: list[dict]


def _role_filter(role: str, value: str) -> tuple[str, list[str]]:
    """Build the shared SQL fragment for MusicBrainz + verified role search."""
    pattern = f"%{value}%"
    return (
        f"""
        AND (
            EXISTS (
                SELECT 1
                FROM song_artists sa
                JOIN artists a ON sa.artist_id = a.artist_id
                WHERE sa.song_id = s.song_id
                  AND sa.role = '{role}'
                  AND a.name ILIKE %s
            )
            OR EXISTS (
                SELECT 1
                FROM verified_song_credits vsc
                JOIN artists a ON vsc.artist_id = a.artist_id
                WHERE vsc.song_id = s.song_id
                  AND vsc.role = '{role}'
                  AND a.name ILIKE %s
            )
        )
        """,
        [pattern, pattern],
    )


def search_songs(
    singer: str | None = None,
    composer: str | None = None,
    lyricist: str | None = None,
    title: str | None = None,
    film: str | None = None,
    language: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[SongSearchResult]:
    query = """
        SELECT DISTINCT
            s.song_id,
            s.title,
            f.title AS film,
            f.release_year,
            l.name AS language
        FROM songs s
        JOIN films f ON s.film_id = f.film_id
        JOIN languages l ON f.language_id = l.language_id
        WHERE 1 = 1
    """
    params: list[object] = []

    for role, value in (
        ("SINGER", singer),
        ("COMPOSER", composer),
        ("LYRICIST", lyricist),
    ):
        if value and value.strip():
            fragment, fragment_params = _role_filter(role, value.strip())
            query += fragment
            params.extend(fragment_params)

    if title and title.strip():
        query += "AND s.title ILIKE %s\n"
        params.append(f"%{title.strip()}%")

    if film and film.strip():
        query += "AND f.title ILIKE %s\n"
        params.append(f"%{film.strip()}%")

    if language and language.strip():
        query += "AND l.name ILIKE %s\n"
        params.append(f"%{language.strip()}%")

    if year_from is not None:
        query += "AND f.release_year >= %s\n"
        params.append(year_from)

    if year_to is not None:
        query += "AND f.release_year <= %s\n"
        params.append(year_to)

    query += "ORDER BY s.title, s.song_id"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

    return [
        SongSearchResult(
            song_id=row[0],
            title=row[1],
            film=row[2],
            release_year=row[3],
            language=row[4],
        )
        for row in rows
    ]


def get_song_details(song_id: int) -> SongDetails | None:
    song_query = """
        SELECT
            s.song_id,
            s.title,
            f.title AS film,
            f.release_year,
            l.name AS language
        FROM songs s
        JOIN films f ON s.film_id = f.film_id
        JOIN languages l ON f.language_id = l.language_id
        WHERE s.song_id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(song_query, (song_id,))
            row = cursor.fetchone()
            if row is None:
                return None

            result = SongDetails(
                song_id=row[0],
                title=row[1],
                film=row[2],
                release_year=row[3],
                language=row[4],
                credited_artists=[],
                singers=[],
                composers=[],
                lyricists=[],
                verified_singers=[],
                verified_composers=[],
                verified_lyricists=[],
                sources=[],
                credited_artist_sources=[],
                verified_sources=[],
            )

            cursor.execute(
                """
                SELECT a.name, sca.source_name, sca.source_record_id, sca.source_url
                FROM song_credited_artists sca
                JOIN artists a ON sca.artist_id = a.artist_id
                WHERE sca.song_id = %s
                ORDER BY a.name, sca.source_name
                """,
                (song_id,),
            )
            for name, source_name, source_record_id, source_url in cursor.fetchall():
                result.credited_artists.append(name)
                result.credited_artist_sources.append(
                    {
                        "source_name": source_name,
                        "source_record_id": source_record_id,
                        "source_url": source_url,
                    }
                )

            cursor.execute(
                """
                SELECT a.name, sa.role
                FROM song_artists sa
                JOIN artists a ON sa.artist_id = a.artist_id
                WHERE sa.song_id = %s
                ORDER BY a.name
                """,
                (song_id,),
            )
            for name, role in cursor.fetchall():
                if role == "SINGER":
                    result.singers.append(name)
                elif role == "COMPOSER":
                    result.composers.append(name)
                elif role == "LYRICIST":
                    result.lyricists.append(name)

            cursor.execute(
                """
                SELECT
                    a.name,
                    vsc.role,
                    vsc.source_name,
                    vsc.source_record_id,
                    vsc.source_url,
                    vsc.notes
                FROM verified_song_credits vsc
                JOIN artists a ON vsc.artist_id = a.artist_id
                WHERE vsc.song_id = %s
                ORDER BY a.name, vsc.source_name
                """,
                (song_id,),
            )
            for (
                name,
                role,
                source_name,
                source_record_id,
                source_url,
                notes,
            ) in cursor.fetchall():
                if role == "SINGER":
                    result.verified_singers.append(name)
                elif role == "COMPOSER":
                    result.verified_composers.append(name)
                elif role == "LYRICIST":
                    result.verified_lyricists.append(name)

                result.verified_sources.append(
                    {
                        "source_name": source_name,
                        "source_record_id": source_record_id,
                        "source_url": source_url,
                        "notes": notes,
                    }
                )

            cursor.execute(
                """
                SELECT source_name, source_record_id, source_url
                FROM song_sources
                WHERE song_id = %s
                ORDER BY source_name, source_record_id
                """,
                (song_id,),
            )
            for source_name, source_record_id, source_url in cursor.fetchall():
                result.sources.append(
                    {
                        "source_name": source_name,
                        "source_record_id": source_record_id,
                        "source_url": source_url,
                    }
                )

            return result
