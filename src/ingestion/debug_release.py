from src.ingestion.musicbrainz_client import get_release


RELEASE_MBID = "9dbbc6ed-aa9e-490e-989f-11b5759a0985"

release = get_release(RELEASE_MBID)

for medium in release.get("media", []):

    for track in medium.get("tracks", []):

        recording = track.get("recording", {})

        if recording.get("title") != "Hangova":
            continue

        print("=" * 70)
        print("TRACK:", track.get("title"))
        print("RECORDING:", recording.get("id"))
        print()

        print("RECORDING RELATIONS:")

        for relation in recording.get("relations", []):

            print(
                "type=",
                relation.get("type"),
                "| target-type=",
                relation.get("target-type"),
                "| artist=",
                relation.get("artist", {}).get("name"),
                "| work=",
                relation.get("work", {}).get("title"),
            )