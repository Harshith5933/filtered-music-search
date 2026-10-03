from src.models.music import Artist


def upsert_language(cursor, name: str, code: str) -> int:
    cursor.execute(
        """
        INSERT INTO languages (name, code)
        VALUES (%s, %s)
        ON CONFLICT (code)
        DO UPDATE SET name = EXCLUDED.name
        RETURNING language_id;
        """,
        (name, code),
    )
    return cursor.fetchone()[0]


def upsert_film(cursor, title: str, release_year: int | None, language_id: int) -> int:
    cursor.execute(
        """
        INSERT INTO films (title, release_year, language_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (title, release_year, language_id)
        DO UPDATE SET title = EXCLUDED.title
        RETURNING film_id;
        """,
        (title, release_year, language_id),
    )
    return cursor.fetchone()[0]


def upsert_song(cursor, title: str, film_id: int) -> int:
    cursor.execute(
        """
        INSERT INTO songs (title, film_id)
        VALUES (%s, %s)
        ON CONFLICT (film_id, title)
        DO UPDATE SET title = EXCLUDED.title
        RETURNING song_id;
        """,
        (title, film_id),
    )
    return cursor.fetchone()[0]


def upsert_artist(cursor, artist: Artist) -> int:
    cursor.execute(
        """
        INSERT INTO artists (mbid, name)
        VALUES (%s, %s)
        ON CONFLICT (mbid)
        DO UPDATE SET name = EXCLUDED.name
        RETURNING artist_id;
        """,
        (artist.mbid, artist.name),
    )
    return cursor.fetchone()[0]


def link_song_artist(cursor, song_id: int, artist_id: int, role: str) -> None:
    cursor.execute(
        """
        INSERT INTO song_artists (song_id, artist_id, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (song_id, artist_id, role)
        DO NOTHING;
        """,
        (song_id, artist_id, role),
    )


def link_song_credited_artist(
    cursor,
    song_id: int,
    artist_id: int,
    source_name: str,
    source_record_id: str,
    source_url: str | None,
) -> None:
    cursor.execute(
        """
        INSERT INTO song_credited_artists (
            song_id,
            artist_id,
            source_name,
            source_record_id,
            source_url
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (song_id, artist_id, source_name, source_record_id)
        DO UPDATE SET source_url = EXCLUDED.source_url;
        """,
        (
            song_id,
            artist_id,
            source_name,
            source_record_id,
            source_url,
        ),
    )


def add_song_source(
    cursor,
    song_id: int,
    source_name: str,
    source_record_id: str,
    source_url: str,
) -> None:
    cursor.execute(
        """
        INSERT INTO song_sources (
            song_id,
            source_name,
            source_record_id,
            source_url
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (source_name, source_record_id)
        DO UPDATE SET
            source_url = EXCLUDED.source_url,
            retrieved_at = CURRENT_TIMESTAMP;
        """,
        (song_id, source_name, source_record_id, source_url),
    )


def add_verified_song_credit(
    cursor,
    song_id: int,
    artist_id: int,
    role: str,
    source_name: str,
    source_record_id: str | None,
    source_url: str,
    notes: str | None = None,
) -> None:
    cursor.execute(
        """
        INSERT INTO verified_song_credits (
            song_id,
            artist_id,
            role,
            source_name,
            source_record_id,
            source_url,
            notes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (song_id, artist_id, role, source_name)
        DO UPDATE SET
            source_record_id = EXCLUDED.source_record_id,
            source_url = EXCLUDED.source_url,
            notes = EXCLUDED.notes,
            verified_at = CURRENT_TIMESTAMP;
        """,
        (
            song_id,
            artist_id,
            role,
            source_name,
            source_record_id,
            source_url,
            notes,
        ),
    )
