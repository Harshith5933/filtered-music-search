from src.ingestion import musicbrainz_parser, release_parser
from src.ingestion.release_parser import parse_release


def test_parse_release_fetches_full_recordings_and_reuses_work_cache(monkeypatch):
    release = {
        "id": "release-1",
        "title": "Example Soundtrack",
        "date": "2026-01-01",
        "media": [
            {
                "tracks": [
                    {"position": "1", "recording": {"id": "rec-1", "title": "Song One"}},
                    {"position": "2", "recording": {"id": "rec-2", "title": "Song Two"}},
                    {"position": "3", "recording": {"id": "rec-1", "title": "Song One"}},
                ]
            }
        ],
    }

    calls = []

    def fake_get_recording(mbid):
        calls.append(mbid)
        return {
            "id": mbid,
            "title": "Song One" if mbid == "rec-1" else "Song Two",
            "artist-credit": [],
            "relations": [
                {
                    "target-type": "work",
                    "type": "performance",
                    "work": {"id": "work-shared", "title": "Shared Work"},
                }
            ],
            "releases": [],
        }

    monkeypatch.setattr(release_parser, "get_recording", fake_get_recording)
    monkeypatch.setattr(
        musicbrainz_parser,
        "get_work",
        lambda mbid: {"id": mbid, "relations": []},
    )

    songs = parse_release(release)

    assert len(songs) == 3
    assert calls == ["rec-1", "rec-2"]
    assert all(song.releases[0].mbid == "release-1" for song in songs)
