import argparse
import csv
import logging
from pathlib import Path

from src.database.connection import get_connection
from src.database.repositories import add_verified_song_credit


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

REQUIRED_COLUMNS = {
    "song_id",
    "artist_mbid",
    "role",
    "source_name",
    "source_record_id",
    "source_url",
    "notes",
}

VALID_ROLES = {"SINGER", "COMPOSER", "LYRICIST"}


def validate_csv(file_path: Path):
    """Read and validate the CSV structure and its records."""

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no header.")

        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing_columns:
            raise ValueError(
                f"Missing required CSV columns: {', '.join(sorted(missing_columns))}"
            )

        rows = []
        for line_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                logging.warning("Skipping empty row at line %d", line_number)
                continue

            row["role"] = (row.get("role") or "").strip().upper()
            row["artist_mbid"] = (row.get("artist_mbid") or "").strip()
            row["source_name"] = (row.get("source_name") or "").strip()
            row["source_url"] = (row.get("source_url") or "").strip()
            row["source_record_id"] = (
                (row.get("source_record_id") or "").strip() or None
            )
            row["notes"] = (row.get("notes") or "").strip() or None

            try:
                row["song_id"] = int(row["song_id"])
                if row["song_id"] <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                raise ValueError(
                    f"Invalid song_id at line {line_number}: "
                    f"{row.get('song_id')!r}"
                )

            if not row["artist_mbid"]:
                raise ValueError(
                    f"Missing artist_mbid at line {line_number}"
                )

            if row["role"] not in VALID_ROLES:
                raise ValueError(
                    f"Invalid role at line {line_number}: {row['role']!r}. "
                    f"Allowed roles: {', '.join(sorted(VALID_ROLES))}"
                )

            if not row["source_name"]:
                raise ValueError(
                    f"Missing source_name at line {line_number}"
                )

            if not row["source_url"]:
                raise ValueError(
                    f"Missing source_url at line {line_number}"
                )

            rows.append((line_number, row))

        return rows


def process_credits(file_path: Path):
    """Validate and insert verified credits in one transaction."""

    rows = validate_csv(file_path)

    if not rows:
        logging.info("No valid data rows found in %s", file_path)
        return

    processed = 0

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                for line_number, row in rows:
                    # Confirm the song exists.
                    cur.execute(
                        "SELECT 1 FROM songs WHERE song_id = %s",
                        (row["song_id"],)
                    )
                    if cur.fetchone() is None:
                        raise ValueError(
                            f"Song ID {row['song_id']} not found "
                            f"(CSV line {line_number})"
                        )

                    # Resolve artist using MusicBrainz ID.
                    cur.execute(
                        "SELECT artist_id FROM artists WHERE mbid = %s",
                        (row["artist_mbid"],)
                    )
                    artist = cur.fetchone()

                    if artist is None:
                        raise ValueError(
                            f"Artist MBID {row['artist_mbid']} not found "
                            f"(CSV line {line_number})"
                        )

                    artist_id = artist[0]

                    # Insert or update through the existing repository function.
                    add_verified_song_credit(
                        cursor=cur,
                        song_id=row["song_id"],
                        artist_id=artist_id,
                        role=row["role"],
                        source_name=row["source_name"],
                        source_record_id=row["source_record_id"],
                        source_url=row["source_url"],
                        notes=row["notes"],
                    )   

                    logging.info(
                        "Processed: song_id=%s, artist_id=%s, role=%s",
                        row["song_id"],
                        artist_id,
                        row["role"],
                    )
                    processed += 1

            conn.commit()
            logging.info("Successfully processed %d credit(s).", processed)

        except Exception:
            conn.rollback()
            logging.exception(
                "Credit ingestion failed. All changes in this run were rolled back."
            )
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Seed verified song credits from a CSV file."
    )
    parser.add_argument(
        "--file",
        default="data/verified_credits.csv",
        help="Path to the verified credits CSV (default: data/verified_credits.csv)"
    )

    args = parser.parse_args()
    csv_path = Path(args.file)

    try:
        process_credits(csv_path)
    except Exception as exc:
        logging.error("%s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

