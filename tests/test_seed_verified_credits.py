
import csv
from pathlib import Path
from unittest.mock import MagicMock, call

# pyrefly: ignore [missing-import]
import pytest

from src.ingestion import seed_verified_credits as seeder


ARTIST_MBID = "b721b996-13ab-439c-9f8e-c51b5c179502"

COLUMNS = [
    "song_id",
    "artist_mbid",
    "role",
    "source_name",
    "source_record_id",
    "source_url",
    "notes",
]



def write_csv(tmp_path: Path, rows, columns=COLUMNS):
    file_path = tmp_path / "test_credits.csv"

    with file_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    return file_path


def valid_row(**overrides):
    row = {
        "song_id": "6",
        "artist_mbid": ARTIST_MBID,
        "role": "LYRICIST",
        "source_name": "Test Source",
        "source_record_id": "",
        "source_url": "https://example.com/credits",
        "notes": "Test credit",
    }
    row.update(overrides)
    return row


def mock_database(monkeypatch, fetchone_results):
    conn = MagicMock()
    conn.__enter__.return_value = conn

    cursor_context = MagicMock()
    cursor = MagicMock()
    cursor_context.__enter__.return_value = cursor
    conn.cursor.return_value = cursor_context

    cursor.fetchone.side_effect = fetchone_results

    monkeypatch.setattr(seeder, "get_connection", lambda: conn)

    return conn, cursor


def test_validate_csv_accepts_valid_row(tmp_path):
    file_path = write_csv(tmp_path, [valid_row()])

    rows = seeder.validate_csv(file_path)

    assert len(rows) == 1
    line_number, row = rows[0]
    assert line_number == 2
    assert row["song_id"] == 6
    assert row["role"] == "LYRICIST"
    assert row["source_name"] == "Test Source"


def test_validate_csv_rejects_invalid_role(tmp_path):
    file_path = write_csv(
        tmp_path,
        [valid_row(role="PRODUCER")],
    )

    with pytest.raises(ValueError, match="Invalid role"):
        seeder.validate_csv(file_path)


def test_validate_csv_rejects_invalid_song_id(tmp_path):
    file_path = write_csv(
        tmp_path,
        [valid_row(song_id="abc")],
    )

    with pytest.raises(ValueError, match="Invalid song_id"):
        seeder.validate_csv(file_path)


def test_validate_csv_rejects_missing_columns(tmp_path):
    file_path = write_csv(
        tmp_path,
        [valid_row()],
        columns=["song_id", "role"],
    )

    with pytest.raises(ValueError, match="Missing required CSV columns"):
        seeder.validate_csv(file_path)


def test_process_credits_commits_valid_credit(tmp_path, monkeypatch):
    file_path = write_csv(tmp_path, [valid_row()])
    conn, cursor = mock_database(
        monkeypatch,
        fetchone_results=[(1,), (65,)],
    )
    insert_mock = MagicMock()
    monkeypatch.setattr(
        seeder, "add_verified_song_credit", insert_mock
    )

    seeder.process_credits(file_path)

    insert_mock.assert_called_once_with(
        cursor=cursor,
        song_id=6,
        artist_id=65,
        role="LYRICIST",
        source_name="Test Source",
        source_record_id=None,
        source_url="https://example.com/credits",
        notes="Test credit",
    )
    conn.commit.assert_called_once()
    conn.rollback.assert_not_called()


def test_process_credits_rolls_back_unknown_artist(
    tmp_path, monkeypatch
):
    file_path = write_csv(
        tmp_path,
        [valid_row(artist_mbid="unknown-mbid")],
    )
    conn, cursor = mock_database(
        monkeypatch,
        fetchone_results=[(1,), None],
    )
    insert_mock = MagicMock()
    monkeypatch.setattr(
        seeder, "add_verified_song_credit", insert_mock
    )

    with pytest.raises(ValueError, match="Artist MBID"):
        seeder.process_credits(file_path)

    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()
    insert_mock.assert_not_called()


def test_process_credits_rolls_back_unknown_song(
    tmp_path, monkeypatch
):
    file_path = write_csv(tmp_path, [valid_row(song_id="99999")])
    conn, cursor = mock_database(
        monkeypatch,
        fetchone_results=[None],
    )
    insert_mock = MagicMock()
    monkeypatch.setattr(
        seeder, "add_verified_song_credit", insert_mock
    )

    with pytest.raises(ValueError, match="Song ID"):
        seeder.process_credits(file_path)

    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()
    insert_mock.assert_not_called()


from src.database.repositories import add_verified_song_credit


def test_add_verified_credit_uses_upsert():
    cursor = MagicMock()

    add_verified_song_credit(
        cursor=cursor,
        song_id=6,
        artist_id=65,
        role="LYRICIST",
        source_name="Test Source",
        source_record_id=None,
        source_url="https://example.com/credits",
        notes="Test credit",
    )

    sql = cursor.execute.call_args[0][0]
    assert "ON CONFLICT" in sql
    assert "DO UPDATE SET" in sql
    normalized_sql = " ".join(sql.split())
    assert "ON CONFLICT (song_id, artist_id, role, source_name)" in normalized_sql


import os
from uuid import uuid4

psycopg2 = pytest.importorskip("psycopg2", reason="PostgreSQL integration test")
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()


def test_postgres_verified_credit_upsert():
    # Safety guard: never run against the main project database.
    test_db = os.getenv("DB_TEST_NAME")
    if test_db != "south_indian_music_test":
        pytest.skip("DB_TEST_NAME must be south_indian_music_test")

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=test_db,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    try:
        with conn.cursor() as cur:
            unique = uuid4().hex
            mbid = str(uuid4())

            cur.execute(
                """
                INSERT INTO languages (name, code)
                VALUES (%s, %s)
                RETURNING language_id
                """,
                (f"Test Language {unique}", f"t{unique[:8]}"),
            )
            language_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO films (title, release_year, language_id)
                VALUES (%s, %s, %s)
                RETURNING film_id
                """,
                (f"Test Film {unique}", 2026, language_id),
            )
            film_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO songs (title, film_id)
                VALUES (%s, %s)
                RETURNING song_id
                """,
                (f"Test Song {unique}", film_id),
            )
            song_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO artists (mbid, name)
                VALUES (%s, %s)
                RETURNING artist_id
                """,
                (mbid, f"Test Artist {unique}"),
            )
            artist_id = cur.fetchone()[0]

            add_verified_song_credit(
                cursor=cur,
                song_id=song_id,
                artist_id=artist_id,
                role="LYRICIST",
                source_name="Integration Test",
                source_record_id=None,
                source_url="https://example.com/first",
                notes="First version",
            )

            # Same unique key, but updated source details.
            add_verified_song_credit(
                cursor=cur,
                song_id=song_id,
                artist_id=artist_id,
                role="LYRICIST",
                source_name="Integration Test",
                source_record_id=None,
                source_url="https://example.com/updated",
                notes="Updated version",
            )

            cur.execute(
                """
                SELECT COUNT(*), MAX(source_url), MAX(notes)
                FROM verified_song_credits
                WHERE song_id = %s
                  AND artist_id = %s
                  AND role = %s
                  AND source_name = %s
                """,
                (song_id, artist_id, "LYRICIST", "Integration Test"),
            )
            count, source_url, notes = cur.fetchone()

            assert count == 1
            assert source_url == "https://example.com/updated"
            assert notes == "Updated version"

    finally:
        # Discard all fixture rows, including related records.
        conn.rollback()
        conn.close()