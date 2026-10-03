from types import SimpleNamespace

from src.database import load_release
from src.models.music import Artist, Song


def test_load_songs_persists_general_and_role_credits(monkeypatch):
    calls = []

    monkeypatch.setattr(
        load_release,
        "upsert_song",
        lambda cursor, title, film_id: 101,
    )
    monkeypatch.setattr(
        load_release,
        "upsert_artist",
        lambda cursor, artist: calls.append(("artist", artist.name)) or 202,
    )
    monkeypatch.setattr(
        load_release,
        "link_song_credited_artist",
        lambda *args: calls.append(("credited", args[1:])),
    )
    monkeypatch.setattr(
        load_release,
        "link_song_artist",
        lambda *args: calls.append(("role", args[1:])),
    )
    monkeypatch.setattr(
        load_release,
        "add_song_source",
        lambda *args: calls.append(("source", args[1:])),
    )

    song = Song(
        recording_mbid="recording-1",
        title="Example",
        credited_artists=[Artist(mbid="a1", name="Credited Artist")],
        singers=[Artist(mbid="a2", name="Singer")],
        composers=[Artist(mbid="a3", name="Composer")],
        lyricists=[],
    )

    summary = load_release.load_songs(SimpleNamespace(), [song], film_id=10)

    assert summary == {
        "songs": 1,
        "credited_artists": 1,
        "role_credits": 2,
        "sources": 1,
    }
    assert any(call[0] == "credited" for call in calls)
    assert any(call[0] == "role" for call in calls)
    assert any(call[0] == "source" for call in calls)
