# Filtered Music Search

A metadata-driven search and data provenance project for South Indian film music. Built using **Python, PostgreSQL, FastAPI, and Streamlit**, the application allows users to search and filter songs based on singers, composers, lyricists, films, languages, and other metadata.

The project focuses on collecting, organizing, validating, and searching structured music metadata. It does **not** host or stream music.

## Features

* **Music metadata ingestion:** Retrieves release, recording, artist, and work metadata from MusicBrainz.
* **Role-based artist credits:** Separates general artist credits from explicitly identified singers, composers, and lyricists.
* **Data provenance:** Maintains source information for independently verified credits.
* **PostgreSQL database:** Stores structured music metadata using relational tables.
* **Multi-filter search:** Search by singer, composer, lyricist, song title, film, language, and year.
* **REST API:** Provides search and retrieval endpoints through FastAPI.
* **Interactive interface:** Uses Streamlit to provide a searchable music metadata interface.
* **Data validation:** Includes validation utilities to identify data-quality issues.
* **Idempotent ingestion:** Prevents duplicate records when the same release is processed repeatedly.
* **Automated testing:** Includes unit, API, and database-related tests.

## Technology Stack

| Component             | Technology     |
| --------------------- | -------------- |
| Programming Language  | Python 3.12    |
| Database              | PostgreSQL     |
| Database Connectivity | psycopg2       |
| Data Validation       | Pydantic       |
| HTTP Requests         | httpx          |
| Backend API           | FastAPI        |
| API Server            | Uvicorn        |
| Frontend              | Streamlit      |
| Data Processing       | Pandas         |
| Testing               | pytest         |
| Version Control       | Git and GitHub |
| Metadata Source       | MusicBrainz    |

## Architecture

```text
       MusicBrainz / Verified Sources
                    |
                    v
          Python Ingestion Layer
       (HTTP, Parsing, Validation)
                    |
                    v
          Data Transformation
                    |
                    v
               PostgreSQL
       +-------------------------+
       | films                   |
       | songs                   |
       | artists                 |
       | song_artists            |
       | song_credited_artists   |
       | verified_song_credits  |
       | song_sources            |
       | youtube_links           |
       +-------------------------+
                    |
                    v
                FastAPI
             (REST Endpoints)
                    |
                    v
              Streamlit UI
           (Search and Filters)
```

### Data Flow

1. **Extraction:** Retrieve release, recording, artist-credit, and work relationship data from MusicBrainz and other verified sources.
2. **Parsing:** Extract relevant metadata from API responses.
3. **Validation:** Validate and normalize the extracted records.
4. **Transformation:** Separate general artist credits from role-specific credits.
5. **Storage:** Store structured metadata and source provenance in PostgreSQL.
6. **API:** Expose search and retrieval functionality through FastAPI.
7. **Presentation:** Display search results and combined filters through the Streamlit interface.

## Data-credit Integrity

A central design principle of this project is that a MusicBrainz `artist-credit` must **not automatically be interpreted as a singer, composer, or lyricist**.

The database maintains these concepts separately:

| Database Table          | Purpose                                                                                                                 |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `song_credited_artists` | Stores artists explicitly listed in a recording's general MusicBrainz artist-credit                                     |
| `song_artists`          | Stores role-specific relationships, such as singers, composers, and lyricists, when supported by explicit relationships |
| `verified_song_credits` | Stores independently verified role-specific credits with source provenance                                              |
| `song_sources`          | Stores information about the sources of music metadata                                                                  |

For example, if MusicBrainz lists an artist on a recording but does not specify their role, the artist is preserved as a credited artist without assigning an unsupported role.

Independently verified credits are stored separately so that their source can be traced and their accuracy reviewed.

## Project Structure

```text
filtered-music-search/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── rejected/
│   ├── verified_credits.csv
│   └── verified_credits_test.csv
│
├── sql/
│   ├── schema.sql
│   └── migrations/
│       └── 001_provenance_tables.sql
│
├── src/
│   ├── api/
│   │   └── main.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── load_release.py
│   │   ├── migrate.py
│   │   ├── repositories.py
│   │   ├── search.py
│   │   ├── validate_data.py
│   │   └── seed_verified_credits.py
│   │
│   ├── frontend/
│   │   └── app.py
│   │
│   ├── ingestion/
│   │   ├── musicbrainz_client.py
│   │   ├── musicbrainz_parser.py
│   │   ├── release_parser.py
│   │   ├── ingest_release.py
│   │   ├── inspect_recording.py
│   │   └── inspect_release.py
│   │
│   ├── models/
│   │   └── music.py
│   │
│   └── services/
│       └── music_search.py
│
├── tests/
│
├── .env.example
├── .gitignore
├── CORRECTIONS.md
├── PROJECT_COMPLETE.md
├── pytest.ini
├── requirements.txt
└── README.md
```

## Prerequisites

Install the following before setting up the project:

* Python 3.12
* PostgreSQL
* Git
* pip

Ensure that PostgreSQL is running and that you have permission to create or access the required databases.

## Installation and Setup

The following instructions use Windows PowerShell and assume that Python is installed and available through the `python` command. If it is not recognized, use `py -3.12` in place of `python`.

### 1. Clone the Repository

```powershell
git clone https://github.com/Harshith5933/filtered-music-search.git
cd filtered-music-search
```

### 2. Create a Virtual Environment

```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, you may need to adjust your execution policy or use another supported activation method.

### 4. Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a local `.env` file from the provided example:

```powershell
Copy-Item .env.example .env
```

Update the `.env` file with your local PostgreSQL configuration.

Example:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=south_indian_music
DB_TEST_NAME=south_indian_music_test
DB_USER=postgres
DB_PASSWORD=your_db_password

MUSIC_API_URL=http://127.0.0.1:8000

LOG_LEVEL=INFO
ENV=development
```

Replace the placeholder password with your own PostgreSQL password.

**Important:** Never commit `.env` or expose database credentials in the repository. The `.gitignore` file excludes the local environment file.

## Database Setup

The project uses PostgreSQL to store films, songs, artists, role-specific credits, general artist credits, and source provenance.

Create the required database or databases in PostgreSQL before running the migration commands.

### Initialize a Fresh Database

For a new database using the project's schema:

```powershell
python -m src.database.migrate
```

### Migrate an Existing Database

If the database already uses the current `artists.mbid` structure and only needs the provenance tables, run:

```powershell
python -m src.database.migrate --migration-only
```

The migration is intentionally guarded. If an old `artists` table has no `mbid` column, the migration stops instead of guessing artist identifiers.

Run database commands only after confirming that your `.env` points to the intended database.

## MusicBrainz Ingestion

The ingestion layer retrieves music metadata from MusicBrainz and parses relevant release, recording, artist-credit, and work relationships.

To ingest a release, run:

```powershell
python -m src.database.load_release `
  --release-mbid <RELEASE_MBID> `
  --film-title "<FILM TITLE>" `
  --year <YEAR> `
  --language "<LANGUAGE>" `
  --language-code <CODE>
```

Replace the placeholders with the actual release MBID, film title, year, language, and language code.

The loader is designed to be idempotent for the project's natural keys and preserves MusicBrainz artist-credit provenance separately from role-bearing relationships.

## Verified Credits

Independently verified role-specific credits are maintained in:

```text
data/verified_credits.csv
```

Each record includes song and artist identifiers, the credited role, source information, and supporting notes.

Only add credits that have been verified from an external source.

To import verified credits, run:

```powershell
python -m src.ingestion.seed_verified_credits
```

The import is transactional. If a record fails validation or the referenced song or artist cannot be resolved, the operation rolls back rather than partially importing the dataset.

The `verified_credits_test.csv` file is reserved for test data and should not be treated as the production verified-credit dataset.

## Data Validation

The project includes a validation command to perform read-only checks against the configured main database.

Run:

```powershell
python -m src.database.validate_data
```

This helps identify data-quality issues without intentionally modifying the database.

## Running the Application

The application consists of two main components:

* **FastAPI:** Backend REST API for searching and retrieving music metadata.
* **Streamlit:** Interactive frontend for searching and filtering music records.

Ensure that the virtual environment is activated before running the application commands.

### 1. Start FastAPI

From the project root, run:

```powershell
python -m uvicorn src.api.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### 2. Available API Endpoints

| Method | Endpoint           | Description               |
| ------ | ------------------ | ------------------------- |
| GET    | `/health`          | Check API health          |
| GET    | `/songs`           | Search and retrieve songs |
| GET    | `/songs/{song_id}` | Retrieve a song by its ID |

### 3. Search with Combined Filters

The `/songs` endpoint supports multiple search filters.

Example:

```text
/songs?singer=Anirudh%20Ravichander&composer=Anirudh%20Ravichander&film=DC
```

All supplied filters use **AND semantics**, meaning that returned songs must satisfy every specified filter.

### 4. Start the Streamlit UI

Open a separate PowerShell terminal, navigate to the project root, and activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Run the frontend:

```powershell
python -m streamlit run src/frontend/app.py
```

The Streamlit interface provides filters for:

* Singer
* Composer
* Lyricist
* Song title
* Film
* Language
* Year

The UI displays MusicBrainz metadata alongside independently verified credits.

## Testing

The project uses pytest for automated testing of its ingestion, parsing, database, repository, and API components.

Run the test suite:

```powershell
python -m pytest -q
```

Database integration tests are configured to use `DB_TEST_NAME` rather than the main `DB_NAME`, helping prevent test operations from modifying the primary dataset.

Ensure that the test database is configured before running tests that require PostgreSQL.

## MusicBrainz Request Handling

The MusicBrainz client includes request-handling features intended to respect API usage requirements:

* Uses a descriptive User-Agent.
* Throttles requests to approximately one request per second.
* Retries HTTP 429 responses.
* Retrieves recording artist and work relationships.
* Retrieves artist relationships from associated works.

The parser distinguishes general artist-credit entries from role-specific relationships. It does not infer a singer, composer, or lyricist role from an artist's name alone.

## Current Project Status

The core MVP has been implemented and tested locally.

* [x] MusicBrainz API client
* [x] Release and recording metadata parsing
* [x] Role-safe artist-credit extraction
* [x] PostgreSQL schema and migrations
* [x] Provenance-preserving database model
* [x] Idempotent release loading
* [x] Independently verified credit layer
* [x] Multi-filter FastAPI search
* [x] Streamlit search interface
* [x] Data validation command
* [x] Automated unit and API tests

The local test suite previously completed with **28 passing tests and one deprecation warning**. Results may vary with subsequent code or environment changes.

## Design Decisions

### Why PostgreSQL?

Music metadata contains interconnected entities such as films, songs, artists, languages, roles, and external sources. PostgreSQL supports relational modeling and constraints that help maintain these relationships consistently.

### Why Separate Artist-credit and Role-specific Credits?

A general artist-credit does not necessarily identify an artist's contribution. Separating artist-credit entries from role-specific relationships reduces unsupported attribution and preserves the distinction between source metadata and verified roles.

### Why FastAPI and Streamlit?

FastAPI exposes search functionality through a REST interface, while Streamlit provides a practical interactive interface for exploring the metadata without building a separate frontend application.

### Why Not Spark, Airflow, or Kafka?

The current project is an MVP with a relatively small dataset and does not require distributed processing or complex orchestration. Tools such as Spark, Airflow, and Kafka can be considered if future data volume, processing complexity, or workload justifies them.

## Limitations

* Metadata coverage depends on the availability and completeness of external sources.
* MusicBrainz may not provide role-specific relationships for every recording.
* Independently verified credits require reliable supporting sources.
* The application provides metadata search and YouTube links where available; it does not host or stream audio.
* Search results are limited by the data currently ingested into the database.

## Future Improvements

Potential extensions include:

* Expanding the verified South Indian music dataset.
* Integrating additional reliable metadata sources.
* Improving artist-alias matching and entity resolution.
* Adding advanced search and sorting capabilities.
* Containerizing the application with Docker.
* Introducing workflow orchestration if ingestion complexity increases.
* Adding deployment and monitoring infrastructure.

These are potential future extensions, not features currently claimed as implemented.

## License

No license has been specified yet. Unless a license is added to the repository, others should not assume they have permission to reuse, modify, or redistribute the project.

## Acknowledgements

* [MusicBrainz](https://musicbrainz.org/) for its open music metadata database and API.
* The open-source communities behind Python, PostgreSQL, FastAPI, Streamlit, and pytest.
