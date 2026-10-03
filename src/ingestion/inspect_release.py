"""Inspect the recording-level relationships embedded in a release response."""

from src.ingestion.musicbrainz_client import get_release

RELEASE_MBID = "9dbbc6ed-aa9e-490e-989f-11b5759a0985"


def main() -> None:
    release = get_release(RELEASE_MBID)

    print(f"Release: {release.get('title')}")
    print(f"MBID: {release.get('id')}")

    for medium in release.get("media", []):
        for track in medium.get("tracks", []):
            recording = track.get("recording")
            if not recording:
                continue

            print(
                f"\nTrack {track.get('position')}: "
                f"{recording.get('title')}"
            )

            relationships = recording.get("relations", [])
            if not relationships:
                print("  No embedded recording relationships.")
                continue

            for relation in relationships:
                relation_type = relation.get("type")

                if relation.get("target-type") == "artist":
                    artist = relation.get("artist", {})
                    print(
                        f"  {relation_type} -> "
                        f"{artist.get('name')} | {artist.get('id')}"
                    )

                elif relation.get("target-type") == "work":
                    work = relation.get("work", {})
                    print(
                        f"  {relation_type} -> WORK "
                        f"{work.get('title')} | {work.get('id')}"
                    )


if __name__ == "__main__":
    main()
