"""Inspect one MusicBrainz recording and its parsed credits."""

from __future__ import annotations

import sys

from src.ingestion.musicbrainz_client import get_recording
from src.ingestion.musicbrainz_parser import parse_recording_data

DEFAULT_RECORDING_MBID = "ce2e93d8-512f-449a-8eaa-0ad9ab051886"


def main() -> None:
    recording_mbid = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RECORDING_MBID

    recording = get_recording(recording_mbid)
    song = parse_recording_data(recording)

    print(f"Title: {song.title}")
    print(f"Recording MBID: {song.recording_mbid}")
    print(f"Work MBID: {song.work_mbid}")

    print("\nCredited artists:")
    for artist in song.credited_artists:
        print(f"  {artist.name} | {artist.mbid}")

    print("\nSingers:")
    for artist in song.singers:
        print(f"  {artist.name} | {artist.mbid}")

    print("\nComposers:")
    for artist in song.composers:
        print(f"  {artist.name} | {artist.mbid}")

    print("\nLyricists:")
    for artist in song.lyricists:
        print(f"  {artist.name} | {artist.mbid}")


if __name__ == "__main__":
    main()
