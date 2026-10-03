from src.ingestion import musicbrainz_parser
from src.ingestion.musicbrainz_parser import (
    parse_recording_data,
    unique_artists,
    unique_releases,
)
from src.models.music import Artist, Release


def make_recording(relations=None):
    return {
        "id": "recording-1",
        "title": "Example Song",
        "artist-credit": [
            {
                "artist": {
                    "id": "artist-credit-1",
                    "name": "Credited Artist",
                }
            }
        ],
        "relations": relations or [],
        "releases": [
            {
                "id": "release-1",
                "title": "Example Release",
                "date": "2026-01-01",
            }
        ],
    }


def test_artist_credit_is_not_automatically_a_singer():
    song = parse_recording_data(make_recording())

    assert [artist.name for artist in song.credited_artists] == [
        "Credited Artist"
    ]
    assert song.singers == []


def test_vocal_relationship_extracts_singer(monkeypatch):
    recording = make_recording(
        relations=[
            {
                "target-type": "artist",
                "type": "vocal",
                "artist": {
                    "id": "singer-1",
                    "name": "Singer One",
                },
            },
            {
                "target-type": "work",
                "type": "performance",
                "work": {
                    "id": "work-1",
                    "title": "Example Song",
                },
            },
        ]
    )

    monkeypatch.setattr(
        musicbrainz_parser,
        "get_work",
        lambda mbid: {"id": mbid, "relations": []},
    )

    song = parse_recording_data(recording)

    assert [artist.name for artist in song.singers] == ["Singer One"]
    assert song.work_mbid == "work-1"


def test_multiple_singers_are_preserved():
    recording = make_recording(
        relations=[
            {
                "target-type": "artist",
                "type": "vocal",
                "artist": {"id": "singer-1", "name": "Singer One"},
            },
            {
                "target-type": "artist",
                "type": "vocal",
                "artist": {"id": "singer-2", "name": "Singer Two"},
            },
        ]
    )

    song = parse_recording_data(recording)

    assert [artist.name for artist in song.singers] == [
        "Singer One",
        "Singer Two",
    ]


def test_composer_and_lyricist_come_from_work(monkeypatch):
    recording = make_recording(
        relations=[
            {
                "target-type": "work",
                "type": "performance",
                "work": {"id": "work-1", "title": "Example Song"},
            }
        ]
    )

    monkeypatch.setattr(
        musicbrainz_parser,
        "get_work",
        lambda mbid: {
            "id": mbid,
            "relations": [
                {
                    "target-type": "artist",
                    "type": "composer",
                    "artist": {"id": "composer-1", "name": "Composer One"},
                },
                {
                    "target-type": "artist",
                    "type": "lyricist",
                    "artist": {"id": "lyricist-1", "name": "Lyricist One"},
                },
            ],
        },
    )

    song = parse_recording_data(recording)

    assert [artist.name for artist in song.composers] == ["Composer One"]
    assert [artist.name for artist in song.lyricists] == ["Lyricist One"]


def test_release_override_is_included_once():
    recording = make_recording()
    override = Release(
        mbid="release-1",
        title="Example Release",
        date="2026-01-01",
    )

    song = parse_recording_data(recording, release_override=override)

    assert len(song.releases) == 1
    assert song.releases[0].mbid == "release-1"


def test_unique_helpers_use_ids():
    artists = [
        Artist(mbid="a", name="Same"),
        Artist(mbid="a", name="Same"),
        Artist(mbid="b", name="Other"),
    ]
    releases = [
        Release(mbid="r", title="Release"),
        Release(mbid="r", title="Release"),
    ]

    assert [artist.mbid for artist in unique_artists(artists)] == ["a", "b"]
    assert [release.mbid for release in unique_releases(releases)] == ["r"]
