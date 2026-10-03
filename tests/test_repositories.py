from unittest.mock import MagicMock

from src.database.repositories import link_song_credited_artist


def test_link_song_credited_artist_uses_provenance_key():
    cursor = MagicMock()

    link_song_credited_artist(
        cursor,
        10,
        20,
        "MusicBrainz",
        "recording-1",
        "https://musicbrainz.org/recording/recording-1",
    )

    sql, params = cursor.execute.call_args[0]
    normalized = " ".join(sql.split())

    assert "song_credited_artists" in normalized
    assert "ON CONFLICT (song_id, artist_id, source_name, source_record_id)" in normalized
    assert params == (
        10,
        20,
        "MusicBrainz",
        "recording-1",
        "https://musicbrainz.org/recording/recording-1",
    )
