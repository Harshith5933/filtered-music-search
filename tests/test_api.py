import os

import pytest
import src.database.search as search
from src.database.connection import get_connection


def connect_to_test_db():
    test_db = os.getenv("DB_TEST_NAME")

    if test_db != "south_indian_music_test":
        raise RuntimeError("Unexpected test database")

    return get_connection(dbname=test_db)



from types import SimpleNamespace

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient

from src.api import main

client = TestClient(main.app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "South Indian Music Search API"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_songs(monkeypatch):
    mock_results = [
        SimpleNamespace(
            song_id=3,
            title="Ain't Nobody",
            film="DC",
            release_year=2026,
            language="Tamil",
        )
    ]

    def mock_search_songs(**kwargs):
        assert kwargs["singer"] == "Anirudh Ravichander"
        assert kwargs["film"] == "DC"
        return mock_results

    monkeypatch.setattr(main, "search_songs", mock_search_songs)

    response = client.get(
        "/songs",
        params={
            "singer": "Anirudh Ravichander",
            "film": "DC",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 1
    assert data["results"][0]["song_id"] == 3
    assert data["results"][0]["title"] == "Ain't Nobody"


def test_song_details(monkeypatch):
    mock_result = SimpleNamespace(
        song_id=6,
        title="Hangova",
        film="DC",
        release_year=2026,
        language="Tamil",
        singers=["Anirudh Ravichander"],
        composers=["Anirudh Ravichander"],
        lyricists=["Anirudh Ravichander"],
        verified_singers=[],
        verified_composers=[],
        verified_lyricists=["Heisenberg"],
        sources=["MusicBrainz"],
        credited_artists=["Anirudh Ravichander"],
        credited_artist_sources=[],
        verified_sources=["YouTube - Sun TV", "Qobuz"],
    )

    monkeypatch.setattr(
        main, "get_song_details", lambda song_id: mock_result
    )

    response = client.get("/songs/6")

    assert response.status_code == 200
    data = response.json()

    assert data["title"] == "Hangova"
    assert data["credits"]["musicbrainz"]["credited_artists"] == [
        "Anirudh Ravichander"
    ]
    assert data["credits"]["musicbrainz"]["lyricists"] == [
        "Anirudh Ravichander"
    ]
    assert data["credits"]["verified"]["lyricists"] == ["Heisenberg"]
    assert "YouTube - Sun TV" in data["verified_sources"]


def test_song_not_found(monkeypatch):
    monkeypatch.setattr(
        main, "get_song_details", lambda song_id: None
    )

    response = client.get("/songs/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Song with ID 9999 not found"



def test_search_api_with_test_database(monkeypatch):
    pytest.importorskip("psycopg2", reason="PostgreSQL integration test")
    monkeypatch.setattr(
        search,
        "get_connection",
        connect_to_test_db
    )

    response = client.get("/songs")

    assert response.status_code == 200