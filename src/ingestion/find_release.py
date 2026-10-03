import httpx

url = "https://musicbrainz.org/ws/2/release/"

response = httpx.get(
    url,
    params={
        "query": 'release:"Devara Part 1"',
        "fmt": "json",
        "limit": 10,
    },
    headers={
        "User-Agent": "SouthIndianMusicSearch/0.1 (personal research project)"
    },
    timeout=30,
)
response.raise_for_status()

for release in response.json().get("releases", []):
    print(
        release.get("id"),
        "|", release.get("title"),
        "|", release.get("date"),
        "|", release.get("status"),
    )