-- SOUTH INDIAN MUSIC SEARCH
-- PostgreSQL schema - V2
-- Metadata-only search application. Safe to re-run on an existing V2 database.
-- No DROP statements.

CREATE TABLE IF NOT EXISTS languages (
    language_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_languages_name UNIQUE (name),
    CONSTRAINT uq_languages_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS films (
    film_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year INT CHECK (release_year BETWEEN 1900 AND 2100),
    language_id INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_films_language
        FOREIGN KEY (language_id)
        REFERENCES languages(language_id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_films_title_year_lang
        UNIQUE (title, release_year, language_id)
);

CREATE TABLE IF NOT EXISTS songs (
    song_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    film_id INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_songs_film
        FOREIGN KEY (film_id)
        REFERENCES films(film_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_songs_film_title
        UNIQUE (film_id, title)
);

CREATE TABLE IF NOT EXISTS artists (
    artist_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mbid VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_artists_mbid UNIQUE (mbid)
);

-- Role-bearing credits. Do not put a general MusicBrainz artist-credit here
-- unless the role is explicitly known.
CREATE TABLE IF NOT EXISTS song_artists (
    song_id INT NOT NULL,
    artist_id INT NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_song_artists
        PRIMARY KEY (song_id, artist_id, role),
    CONSTRAINT fk_song_artists_song
        FOREIGN KEY (song_id)
        REFERENCES songs(song_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_song_artists_artist
        FOREIGN KEY (artist_id)
        REFERENCES artists(artist_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_song_artists_role
        CHECK (role IN ('SINGER', 'COMPOSER', 'LYRICIST', 'MUSIC_DIRECTOR'))
);

-- General MusicBrainz artist-credit entries with provenance. No role is inferred.
CREATE TABLE IF NOT EXISTS song_credited_artists (
    song_id INT NOT NULL,
    artist_id INT NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_record_id VARCHAR(255) NOT NULL,
    source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_song_credited_artists
        PRIMARY KEY (song_id, artist_id, source_name, source_record_id),
    CONSTRAINT fk_song_credited_artists_song
        FOREIGN KEY (song_id)
        REFERENCES songs(song_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_song_credited_artists_artist
        FOREIGN KEY (artist_id)
        REFERENCES artists(artist_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS artist_aliases (
    alias_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    artist_id INT NOT NULL,
    alias VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_artist_aliases_artist
        FOREIGN KEY (artist_id)
        REFERENCES artists(artist_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_artist_aliases_artist_alias
        UNIQUE (artist_id, alias)
);

CREATE TABLE IF NOT EXISTS song_sources (
    source_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    song_id INT NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_record_id VARCHAR(255) NOT NULL,
    source_url TEXT,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_song_sources_song
        FOREIGN KEY (song_id)
        REFERENCES songs(song_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_song_sources_lineage
        UNIQUE (source_name, source_record_id)
);

-- Independently verified role credits, with explicit source provenance.
CREATE TABLE IF NOT EXISTS verified_song_credits (
    credit_id BIGSERIAL PRIMARY KEY,
    song_id INT NOT NULL,
    artist_id INT NOT NULL,
    role VARCHAR(50) NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_record_id VARCHAR(255),
    source_url TEXT NOT NULL,
    notes TEXT,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_verified_song_credits_song
        FOREIGN KEY (song_id)
        REFERENCES songs(song_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_verified_song_credits_artist
        FOREIGN KEY (artist_id)
        REFERENCES artists(artist_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_verified_song_credits_role
        CHECK (role IN ('SINGER', 'COMPOSER', 'LYRICIST')),
    CONSTRAINT uq_verified_song_credit
        UNIQUE (song_id, artist_id, role, source_name)
);

CREATE TABLE IF NOT EXISTS youtube_links (
    youtube_link_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    song_id INT NOT NULL,
    video_id VARCHAR(64) NOT NULL,
    url TEXT NOT NULL,
    channel_name VARCHAR(255),
    is_official BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_youtube_links_video_id UNIQUE (video_id),
    CONSTRAINT fk_youtube_links_song
        FOREIGN KEY (song_id)
        REFERENCES songs(song_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_films_language_id ON films(language_id);
CREATE INDEX IF NOT EXISTS idx_songs_film_id ON songs(film_id);
CREATE INDEX IF NOT EXISTS idx_song_artists_artist_id ON song_artists(artist_id);
CREATE INDEX IF NOT EXISTS idx_song_artists_role ON song_artists(role);
CREATE INDEX IF NOT EXISTS idx_song_credited_artists_artist_id
    ON song_credited_artists(artist_id);
CREATE INDEX IF NOT EXISTS idx_artist_aliases_artist_id
    ON artist_aliases(artist_id);
CREATE INDEX IF NOT EXISTS idx_song_sources_song_id
    ON song_sources(song_id);
CREATE INDEX IF NOT EXISTS idx_youtube_links_song_id
    ON youtube_links(song_id);
CREATE INDEX IF NOT EXISTS idx_verified_song_credits_song_id
    ON verified_song_credits(song_id);
CREATE INDEX IF NOT EXISTS idx_verified_song_credits_artist_id
    ON verified_song_credits(artist_id);
CREATE INDEX IF NOT EXISTS idx_verified_song_credits_role
    ON verified_song_credits(role);
CREATE INDEX IF NOT EXISTS idx_films_release_year ON films(release_year);
CREATE INDEX IF NOT EXISTS idx_films_title ON films(title);
CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title);
CREATE INDEX IF NOT EXISTS idx_artists_name ON artists(name);
CREATE INDEX IF NOT EXISTS idx_artist_aliases_alias ON artist_aliases(alias);
