import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ingestion.musicbrainz_client import get_work


WORKS = {
    "Ain't Nobody": "a17eea4e-061e-4a40-aa60-a8943396590f",
    "Hangova": "97d40cf5-5750-4cc1-8979-959e2f245ce7",
    "Vizhigale": "2f7d5131-b13f-4e19-a795-e19b065375de",
}


for title, work_mbid in WORKS.items():

    print("=" * 70)
    print(title)
    print("WORK:", work_mbid)

    work = get_work(work_mbid)

    for relation in work.get("relations", []):

        if relation.get("target-type") != "artist":
            continue

        artist = relation.get("artist", {})

        print(
            "TYPE:",
            relation.get("type"),
            "| ARTIST:",
            artist.get("name"),
            "| MBID:",
            artist.get("id"),
        )