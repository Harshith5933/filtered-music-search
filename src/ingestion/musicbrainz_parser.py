"""Transform MusicBrainz recording data into project domain models."""

from __future__ import annotations

from src.ingestion.musicbrainz_client import get_recording, get_work
from src.models.music import Artist, Release, Song


def _artist_from_payload(payload: dict | None) -> Artist | None:
    """Build an Artist model when an embedded artist payload is usable."""

    if not payload:
        return None

    mbid = payload.get("id")
    name = payload.get("name")

    if not mbid or not name:
        return None

    return Artist(mbid=mbid, name=name)


def unique_artists(artists: list[Artist]) -> list[Artist]:
    """Keep the first occurrence of each artist MBID."""

    seen: set[str] = set()
    result: list[Artist] = []

    for artist in artists:
        if artist.mbid in seen:
            continue

        seen.add(artist.mbid)
        result.append(artist)

    return result


def unique_releases(releases: list[Release]) -> list[Release]:
    """Keep the first occurrence of each release MBID."""

    seen: set[str] = set()
    result: list[Release] = []

    for release in releases:
        if release.mbid in seen:
            continue

        seen.add(release.mbid)
        result.append(release)

    return result


def _extract_credited_artists(recording: dict) -> list[Artist]:
    """Extract artists explicitly present in the recording artist-credit."""

    artists: list[Artist] = []

    for credit in recording.get("artist-credit", []):
        artist = _artist_from_payload(credit.get("artist"))
        if artist:
            artists.append(artist)

    return unique_artists(artists)


def _extract_singers(recording: dict) -> list[Artist]:
    """Extract explicit recording -> artist vocal relationships."""

    singers: list[Artist] = []

    for relation in recording.get("relations", []):
        if relation.get("target-type") != "artist":
            continue

        if relation.get("type") != "vocal":
            continue

        artist = _artist_from_payload(relation.get("artist"))
        if artist:
            singers.append(artist)

    return unique_artists(singers)


def _find_work_mbid(recording: dict) -> str | None:
    """Find the Work targeted by the recording's performance relationship."""

    for relation in recording.get("relations", []):
        if relation.get("target-type") != "work":
            continue

        if relation.get("type") != "performance":
            continue

        work = relation.get("work")
        if work and work.get("id"):
            return work["id"]

    return None


def _extract_work_credits(
    work: dict | None,
) -> tuple[list[Artist], list[Artist]]:
    """Return composer and lyricist artists from a Work response."""

    composers: list[Artist] = []
    lyricists: list[Artist] = []

    if not work:
        return composers, lyricists

    for relation in work.get("relations", []):
        if relation.get("target-type") != "artist":
            continue

        artist = _artist_from_payload(relation.get("artist"))
        if not artist:
            continue

        relation_type = relation.get("type")

        if relation_type == "composer":
            composers.append(artist)
        elif relation_type == "lyricist":
            lyricists.append(artist)

    return unique_artists(composers), unique_artists(lyricists)


def _extract_releases(recording: dict) -> list[Release]:
    """Convert linked MusicBrainz releases into Release models."""

    releases: list[Release] = []

    for payload in recording.get("releases", []):
        mbid = payload.get("id")
        title = payload.get("title")

        if not mbid or not title:
            continue

        releases.append(
            Release(
                mbid=mbid,
                title=title,
                date=payload.get("date"),
            )
        )

    return unique_releases(releases)


def parse_recording_data(
    recording: dict,
    *,
    work: dict | None = None,
    work_cache: dict[str, dict] | None = None,
    release_override: Release | None = None,
) -> Song:
    """Parse an already-fetched recording response into a Song model.

    Singer credits are taken from explicit recording-level ``vocal``
    relationships. Composer and lyricist credits are taken from the linked
    Work. This keeps the two levels of MusicBrainz metadata separate.
    """

    recording_mbid = recording.get("id")
    title = recording.get("title")

    if not recording_mbid or not title:
        raise ValueError("Recording must contain both 'id' and 'title'.")

    credited_artists = _extract_credited_artists(recording)
    singers = _extract_singers(recording)
    work_mbid = _find_work_mbid(recording)

    if work_mbid and work is None:
        if work_cache is None:
            work_cache = {}

        if work_mbid not in work_cache:
            work_cache[work_mbid] = get_work(work_mbid)

        work = work_cache[work_mbid]

    composers, lyricists = _extract_work_credits(work)

    releases = _extract_releases(recording)
    if release_override:
        releases = unique_releases([release_override, *releases])

    return Song(
        recording_mbid=recording_mbid,
        work_mbid=work_mbid,
        title=title,
        credited_artists=credited_artists,
        singers=singers,
        composers=composers,
        lyricists=lyricists,
        releases=releases,
    )


def parse_recording(
    recording_mbid: str,
    *,
    work_cache: dict[str, dict] | None = None,
) -> Song:
    """Fetch and parse one MusicBrainz recording by MBID."""

    recording = get_recording(recording_mbid)
    return parse_recording_data(recording, work_cache=work_cache)
