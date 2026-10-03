"""Parse a MusicBrainz Release into Song domain models."""

from __future__ import annotations

from src.ingestion.musicbrainz_client import get_recording
from src.ingestion.musicbrainz_parser import parse_recording_data
from src.models.music import Release, Song


def parse_release(release: dict) -> list[Song]:
    """Parse all usable recordings belonging to one MusicBrainz Release."""

    release_mbid = release.get("id")
    release_title = release.get("title")

    if not release_mbid or not release_title:
        raise ValueError("Release must contain both 'id' and 'title'.")

    release_obj = Release(
        mbid=release_mbid,
        title=release_title,
        date=release.get("date"),
    )

    songs: list[Song] = []
    work_cache: dict[str, dict] = {}
    recording_cache: dict[str, dict] = {}

    for medium in release.get("media", []):
        for track in medium.get("tracks", []):
            recording = track.get("recording")
            if not recording:
                continue

            recording_mbid = recording.get("id")
            if not recording_mbid:
                continue

            if recording_mbid not in recording_cache:
                recording_cache[recording_mbid] = get_recording(recording_mbid)

            full_recording = recording_cache[recording_mbid]

            song = parse_recording_data(
                full_recording,
                work_cache=work_cache,
                release_override=release_obj,
            )
            songs.append(song)

    return songs
