from pathlib import Path


SCHEMA = Path("sql/schema.sql").read_text(encoding="utf-8")


def test_schema_contains_required_provenance_objects():
    assert "CREATE TABLE IF NOT EXISTS song_credited_artists" in SCHEMA
    assert "CREATE TABLE IF NOT EXISTS verified_song_credits" in SCHEMA
    assert "mbid VARCHAR(36) NOT NULL" in SCHEMA
    assert "song_credited_artists" in SCHEMA
    assert "verified_song_credits" in SCHEMA
