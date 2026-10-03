
import httpx
import json

mbid = "b91b89fd-01dd-432c-8724-d2cb5f4fef2a"

url = f"https://musicbrainz.org/ws/2/recording/{mbid}"

response = httpx.get(
    url,
    params={
        "fmt": "json",
        "inc": "artists+artist-credits+releases+work-rels+artist-rels+work-level-rels",
    },
    headers={
        "User-Agent": "SouthIndianMusicSearch/0.1 (personal research project)"
    },
    timeout=30,
)
response.raise_for_status()

data = response.json()

print("Title:", data.get("title"))
print("Artist credits:")
print(json.dumps(data.get("artist-credit", []), indent=2))
print("Relationships:")
print(json.dumps(data.get("relations", []), indent=2))