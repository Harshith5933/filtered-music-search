
import os
import pytest

psycopg2 = pytest.importorskip("psycopg2")
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()


def get_test_connection():
    test_db = os.getenv("DB_TEST_NAME")

    if test_db != "south_indian_music_test":
        raise RuntimeError(
            "Integration tests must use south_indian_music_test. "
            "Set DB_TEST_NAME explicitly."
        )

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=test_db,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def test_connection_targets_test_database():
    conn = get_test_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            database_name = cur.fetchone()[0]

        assert database_name == "south_indian_music_test"
    finally:
        conn.close()