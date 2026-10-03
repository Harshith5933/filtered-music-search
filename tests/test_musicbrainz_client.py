# pyrefly: ignore [missing-import]
import httpx

from src.ingestion import musicbrainz_client


def test_get_recording_requests_artist_relationships(monkeypatch):
    captured = {}

    def fake_get(url, *, params, headers, timeout):
        captured.update(url=url, params=params, headers=headers, timeout=timeout)
        return httpx.Response(200, request=httpx.Request("GET", url), json={"id": "recording-1"})

    monkeypatch.setattr(musicbrainz_client.httpx, "get", fake_get)
    monkeypatch.setattr(musicbrainz_client, "_last_request_at", 0.0)
    monkeypatch.setattr(musicbrainz_client, "REQUEST_DELAY_SECONDS", 0.0)

    musicbrainz_client.get_recording("recording-1")

    assert captured["params"]["inc"] == (
    "artist-credits+releases+work-rels+artist-rels+work-level-rels"
)



def test_get_release_requests_recording_level_relationships(monkeypatch):
    captured = {}

    def fake_get(url, *, params, headers, timeout):
        captured.update(url=url, params=params, headers=headers, timeout=timeout)
        return httpx.Response(200, request=httpx.Request("GET", url), json={"id": "release-1"})

    monkeypatch.setattr(musicbrainz_client.httpx, "get", fake_get)
    monkeypatch.setattr(musicbrainz_client, "_last_request_at", 0.0)
    monkeypatch.setattr(musicbrainz_client, "REQUEST_DELAY_SECONDS", 0.0)

    musicbrainz_client.get_release("release-1")

    assert captured["params"]["inc"] == (
    "recordings+artist-credits+recording-level-rels+work-rels+work-level-rels"
)

