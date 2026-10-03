"""Small synchronous client for the MusicBrainz Web Service API."""

from __future__ import annotations

import time

import httpx


BASE_URL = "https://musicbrainz.org/ws/2"
USER_AGENT = "SouthIndianMusicSearch/0.1 (personal research project)"

REQUEST_DELAY_SECONDS = 1.05
MAX_429_RETRIES = 2

_last_request_at = 0.0


def _throttle() -> None:
    """Keep requests at or below the MusicBrainz public API rate guidance."""

    global _last_request_at

    elapsed = time.monotonic() - _last_request_at

    if elapsed < REQUEST_DELAY_SECONDS:
        time.sleep(REQUEST_DELAY_SECONDS - elapsed)


def _request_json(path: str, params: dict[str, str]) -> dict:
    """Perform one GET request and return the decoded JSON object."""

    global _last_request_at

    url = f"{BASE_URL}/{path}"

    for attempt in range(MAX_429_RETRIES + 1):

        _throttle()

        response = httpx.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )

        _last_request_at = time.monotonic()

        if response.status_code != 429 or attempt == MAX_429_RETRIES:
            response.raise_for_status()
            return response.json()

        retry_after = response.headers.get("Retry-After", "1")

        try:
            retry_seconds = max(
                float(retry_after),
                REQUEST_DELAY_SECONDS,
            )
        except ValueError:
            retry_seconds = REQUEST_DELAY_SECONDS

        time.sleep(retry_seconds)

    raise RuntimeError(
        "MusicBrainz request failed after retries"
    )


def get_recording(recording_mbid: str) -> dict:
    """
    Fetch one recording.

    Includes:
    - artist credits
    - releases
    - recording -> work relationships
    - recording -> artist relationships
    - relationships belonging to linked works
    """

    return _request_json(
        f"recording/{recording_mbid}",
        {
            "fmt": "json",
            "inc": (
                "artist-credits"
                "+releases"
                "+work-rels"
                "+artist-rels"
                "+work-level-rels"
            ),
        },
    )


def get_work(work_mbid: str) -> dict:
    """Fetch one work, including its artist relationships."""

    return _request_json(
        f"work/{work_mbid}",
        {
            "fmt": "json",
            "inc": "artist-rels",
        },
    )


def get_release(release_mbid: str) -> dict:
    """
    Fetch one release with tracks, recording relationships,
    and relationships belonging to the works linked to those recordings.
    """

    return _request_json(
        f"release/{release_mbid}",
        {
            "fmt": "json",
            "inc": (
                "recordings"
                "+artist-credits"
                "+recording-level-rels"
                "+work-rels"
                "+work-level-rels"
            ),
        },
    )