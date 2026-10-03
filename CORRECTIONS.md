# Final correction and review notes

The project was reviewed across ingestion, parsing, persistence, search, API, UI, schema and tests rather than fixing only the last failing file.

## Corrected data-model issue

The parser already preserved `credited_artists`, but the database loader discarded them when a MusicBrainz recording had no explicit role relationships. The project now stores those general credits in `song_credited_artists` with source and recording provenance.

Role-bearing `song_artists` remains restricted to explicit `SINGER`, `COMPOSER`, `LYRICIST` and `MUSIC_DIRECTOR` values. This prevents a general artist-credit entry from being silently reclassified as a singer or another role.

## Corrected schema drift

The uploaded project schema did not fully match the Python database code: the loader expected artist MBIDs and the search layer expected `verified_song_credits`, while the schema file did not define all of those objects. `sql/schema.sql` is now the canonical V2 schema and includes both provenance tables and the `artists.mbid` contract.

For an existing V1-style database, `sql/migrations/001_provenance_tables.sql` adds the provenance tables and checks that `artists.mbid` exists before proceeding.

## Corrected repository issues

- Removed duplicate `add_verified_song_credit()` definitions.
- Added `link_song_credited_artist()`.
- Changed source upserts to refresh their URL/retrieval timestamp when the same lineage is ingested again.
- Kept MBID-based artist identity.

## Corrected database loading

`load_release.py` now:

- persists general MusicBrainz artist-credit entries;
- persists role-specific credits separately;
- keeps MusicBrainz source lineage per recording;
- returns an ingestion summary;
- keeps the existing release parsing/cache behavior.

## Corrected search/API/UI

- Added general credited-artist visibility to song details.
- Preserved MusicBrainz and independently verified role credits as separate layers.
- Added API-side validation for inverted year ranges.
- Added configurable `MUSIC_API_URL` for Streamlit.
- Removed duplicated FastAPI imports and formatting inconsistencies.

## Corrected dependency declaration

`requirements.txt` now includes every runtime dependency used by the application, including FastAPI, Uvicorn, Streamlit and Requests.

## Corrected test discovery

The old database demo scripts under `src/database/` used `test_*.py` names even though they were manual scripts. Those names caused pytest collection problems. The final package excludes those stale manual test files; actual automated tests live under `tests/`.

## Validation performed in this review

- Static inspection of all application layers and schema.
- Python source compilation for the final package.
- Unit/API test suite excluding PostgreSQL integration where the review container could not access the user's Windows PostgreSQL instance.
- Schema consistency checks between repository SQL and the canonical schema.

The review environment could not directly connect to the user's local Windows PostgreSQL service, so the final artifact does **not** claim that the user's live main/test databases were mutated or re-verified from this environment.
