# South Indian Music Search

A metadata search and provenance project for South Indian film music. The application stores structured song, film, artist, role-credit and source metadata; it does **not** stream music.

## Architecture

```text
MusicBrainz / verified external sources
                |
                v
        Python ingestion layer
        (HTTP + parsing + validation)
                |
                v
           PostgreSQL
     +-------------------------+
     | films / songs           |
     | artists                 |
     | song_artists            |  <- explicit roles only
     | song_credited_artists   |  <- general artist-credit
     | verified_song_credits   |  <- independently verified roles
     | song_sources            |
     | youtube_links           |
     +-------------------------+
                |
                v
             FastAPI
                |
                v
           Streamlit UI
```

## Data-credit rule

The most important data-quality rule is that a MusicBrainz `artist-credit` is **not automatically a singer, composer or lyricist**.

The ingestion layer stores three concepts separately:

1. `credited_artists`: artists explicitly present in the recording's MusicBrainz artist-credit.
2. `singers`, `composers`, `lyricists`: role-specific credits only when supported by explicit MusicBrainz relationships.
3. `verified_song_credits`: role-specific credits independently verified from another source and stored with provenance.

For example, if MusicBrainz lists an artist on a recording but supplies no role relationship, the artist is preserved as a credited artist without inventing a role.

## Project structure

```text
musicproj_corrected/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── rejected/
│   ├── verified_credits.csv
│   └── verified_credits_test.csv
├── sql/
│   ├── schema.sql
│   └── migrations/
│       └── 001_provenance_tables.sql
├── src/
│   ├── api/main.py
│   ├── database/
│   │   ├── connection.py
│   │   ├── load_release.py
│   │   ├── migrate.py
│   │   ├── repositories.py
│   │   ├── search.py
│   │   ├── seed_verified_credits.py
│   │   └── validate_data.py
│   ├── frontend/app.py
│   ├── ingestion/
│   │   ├── musicbrainz_client.py
│   │   ├── musicbrainz_parser.py
│   │   └── release_parser.py
│   └── models/music.py
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Setup on Windows PowerShell

From the project root:

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and fill in your PostgreSQL password. Do not commit `.env`.

### Database initialization

For a fresh database:

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m src.database.migrate
```

For an existing database that already uses the current `artists.mbid` structure and only needs the provenance tables:

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m src.database.migrate --migration-only
```

The migration is intentionally guarded: if an old `artists` table has no `mbid` column, the migration stops instead of guessing artist identifiers.

## Ingest a MusicBrainz release

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m src.database.load_release `
  --release-mbid <RELEASE_MBID> `
  --film-title "<FILM TITLE>" `
  --year <YEAR> `
  --language "<LANGUAGE>" `
  --language-code <CODE>
```

The loader is idempotent for the project's natural keys and preserves MusicBrainz artist-credit provenance separately from role-bearing relationships.

## Verified credits

Populate `data/verified_credits.csv` only with externally verified role credits. Then run:

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m src.ingestion.seed_verified_credits
```

The import is transactional: if a row fails validation or cannot resolve its song/artist, the run rolls back.

## Data validation

Run the read-only checks against the main database:

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m src.database.validate_data
```

## API

Start FastAPI:

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn src.api.main:app --reload
```

Then open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

Main endpoints:

```text
GET /health
GET /songs
GET /songs/{song_id}
```

Example combined search:

```text
/songs?singer=Anirudh%20Ravichander&composer=Anirudh%20Ravichander&film=DC
```

All supplied filters use AND semantics.

## Streamlit UI

Start the frontend after the API is running:

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m streamlit run src/frontend/app.py
```

The UI exposes singer, composer, lyricist, title, film, language and year filters and shows both MusicBrainz metadata and independently verified credits.

## Tests

Run the unit test suite:

```powershell
C:\Users\harsh\AppData\Local\Programs\Python\Python312\python.exe -m pytest -q
```

Database integration tests intentionally target `DB_TEST_NAME`, not `DB_NAME`.

## MusicBrainz request behavior

The client uses a descriptive User-Agent, throttles requests to roughly one request per second, and retries HTTP 429 responses. Recording requests retrieve artist and work relationships; Work requests retrieve artist relationships. The parser does not infer roles from names or from the general artist-credit field.

## Project status

Core MVP is complete:

- MusicBrainz client
- release and recording parsing
- role-safe credit extraction
- provenance-preserving database model
- idempotent PostgreSQL loading
- independent verified-credit layer
- multi-filter FastAPI search
- Streamlit search UI
- data-quality validation command
- automated unit/API tests

Additional infrastructure such as Spark, Airflow, Kafka or Kubernetes is deliberately not included until data volume or workload requires it.
