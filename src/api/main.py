from fastapi import FastAPI, HTTPException

from src.database.search import get_song_details, search_songs

app = FastAPI(
    title="South Indian Music Search API",
    version="1.0.0",
    description="Search South Indian film-music metadata and credit provenance.",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "South Indian Music Search API",
        "version": "1.0.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/songs")
def songs(
    singer: str | None = None,
    composer: str | None = None,
    lyricist: str | None = None,
    title: str | None = None,
    film: str | None = None,
    language: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
):
    """Search songs. All supplied filters are combined with AND semantics."""
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(
            status_code=422,
            detail="year_from cannot be greater than year_to",
        )

    results = search_songs(
        singer=singer,
        composer=composer,
        lyricist=lyricist,
        title=title,
        film=film,
        language=language,
        year_from=year_from,
        year_to=year_to,
    )

    return {
        "count": len(results),
        "results": [
            {
                "song_id": result.song_id,
                "title": result.title,
                "film": result.film,
                "release_year": result.release_year,
                "language": result.language,
            }
            for result in results
        ],
    }


@app.get("/songs/{song_id}")
def song_details(song_id: int):
    result = get_song_details(song_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Song with ID {song_id} not found",
        )

    return {
        "song_id": result.song_id,
        "title": result.title,
        "film": result.film,
        "release_year": result.release_year,
        "language": result.language,
        "credits": {
            "musicbrainz": {
                "credited_artists": result.credited_artists,
                "singers": result.singers,
                "composers": result.composers,
                "lyricists": result.lyricists,
            },
            "verified": {
                "singers": result.verified_singers,
                "composers": result.verified_composers,
                "lyricists": result.verified_lyricists,
            },
        },
        "sources": result.sources,
        "credited_artist_sources": result.credited_artist_sources,
        "verified_sources": result.verified_sources,
    }
