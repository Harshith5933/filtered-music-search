"""Ingest one MusicBrainz release into PostgreSQL."""

from __future__ import annotations

import argparse

from src.database.connection import get_connection
from src.database.repositories import (
    add_song_source,
    link_song_artist,
    link_song_credited_artist,
    upsert_artist,
    upsert_film,
    upsert_language,
    upsert_song,
)
from src.ingestion.musicbrainz_client import get_release
from src.ingestion.release_parser import parse_release

SOURCE_NAME = "MusicBrainz"


def load_songs(
    cursor,
    songs,
    *,
    film_id: int,
) -> dict[str, int]:
    """Persist parsed songs and return a small ingestion summary."""

    summary = {
        "songs": 0,
        "credited_artists": 0,
        "role_credits": 0,
        "sources": 0,
    }

    for song in songs:
        song_id = upsert_song(cursor, song.title, film_id)
        summary["songs"] += 1

        for artist in song.credited_artists:
            artist_id = upsert_artist(cursor, artist)
            link_song_credited_artist(
                cursor,
                song_id,
                artist_id,
                SOURCE_NAME,
                song.recording_mbid,
                f"https://musicbrainz.org/recording/{song.recording_mbid}",
            )
            summary["credited_artists"] += 1

        for role, artists in (
            ("SINGER", song.singers),
            ("COMPOSER", song.composers),
            ("LYRICIST", song.lyricists),
        ):
            for artist in artists:
                artist_id = upsert_artist(cursor, artist)
                link_song_artist(cursor, song_id, artist_id, role)
                summary["role_credits"] += 1

        add_song_source(
            cursor,
            song_id,
            SOURCE_NAME,
            song.recording_mbid,
            f"https://musicbrainz.org/recording/{song.recording_mbid}",
        )
        summary["sources"] += 1

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load one MusicBrainz release into PostgreSQL."
    )
    parser.add_argument("--release-mbid", required=True)
    parser.add_argument("--film-title", required=True)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--language", required=True)
    parser.add_argument("--language-code", required=True)
    args = parser.parse_args()

    print("Fetching release...")
    release = get_release(args.release_mbid)
    print(f"Release: {release['title']} | {release['id']}")

    songs = parse_release(release)
    print(f"Songs extracted: {len(songs)}")

    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                language_id = upsert_language(
                    cursor,
                    args.language,
                    args.language_code,
                )
                film_id = upsert_film(
                    cursor,
                    args.film_title,
                    args.year,
                    language_id,
                )
                summary = load_songs(
                    cursor,
                    songs,
                    film_id=film_id,
                )
    finally:
        connection.close()

    print("Database loading completed.")
    print(
        "Summary: "
        f"songs={summary['songs']}, "
        f"credited_artists={summary['credited_artists']}, "
        f"role_credits={summary['role_credits']}, "
        f"sources={summary['sources']}"
    )


if __name__ == "__main__":
    main()
