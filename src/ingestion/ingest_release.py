"""Run the MusicBrainz release ingestion demonstration."""

from src.ingestion.musicbrainz_client import get_release
from src.ingestion.release_parser import parse_release


RELEASE_MBID = "9dbbc6ed-aa9e-490e-989f-11b5759a0985"


def print_artists(label: str, artists) -> None:
    print(f"{label}:")

    if not artists:
        print("  None")
        return

    for artist in artists:
        print(f"  {artist.name} | {artist.mbid}")


def main() -> None:
    print("Fetching release...")
    release = get_release(RELEASE_MBID)

    print(f"Release: {release['title']}")
    print(f"Release MBID: {release['id']}")

    songs = parse_release(release)

    print(f"Songs extracted: {len(songs)}")
    print("=" * 70)

    for song in songs:
        print(f"\nSONG: {song.title}")
        print(f"Recording: {song.recording_mbid}")
        print(f"Work: {song.work_mbid}")

        print_artists("CREDITED ARTISTS", song.credited_artists)
        print_artists("SINGERS", song.singers)
        print_artists("COMPOSERS", song.composers)
        print_artists("LYRICISTS", song.lyricists)

        print("RELEASES:")
        if song.releases:
            for release_obj in song.releases:
                print(
                    f"  {release_obj.title} | "
                    f"{release_obj.date} | "
                    f"{release_obj.mbid}"
                )
        else:
            print("  None")

        print("-" * 70)

    print(f"\nTOTAL SONGS: {len(songs)}")
    print(
        "Songs with no explicit singer relationship: "
        f"{sum(not song.singers for song in songs)}"
    )
    print(
        "Songs with multiple singers: "
        f"{sum(len(song.singers) > 1 for song in songs)}"
    )


if __name__ == "__main__":
    main()
