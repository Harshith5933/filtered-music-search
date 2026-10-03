-- Existing-database migration for the provenance additions in schema V2.
-- Safe to re-run. This migration assumes the existing artists table already
-- contains the MBID column used by the current application.

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
        FOREIGN KEY (song_id) REFERENCES songs(song_id) ON DELETE CASCADE,
    CONSTRAINT fk_song_credited_artists_artist
        FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE RESTRICT
);

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
        FOREIGN KEY (song_id) REFERENCES songs(song_id) ON DELETE CASCADE,
    CONSTRAINT fk_verified_song_credits_artist
        FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE RESTRICT,
    CONSTRAINT chk_verified_song_credits_role
        CHECK (role IN ('SINGER', 'COMPOSER', 'LYRICIST')),
    CONSTRAINT uq_verified_song_credit
        UNIQUE (song_id, artist_id, role, source_name)
);

CREATE INDEX IF NOT EXISTS idx_song_credited_artists_artist_id
    ON song_credited_artists(artist_id);
CREATE INDEX IF NOT EXISTS idx_verified_song_credits_song_id
    ON verified_song_credits(song_id);
CREATE INDEX IF NOT EXISTS idx_verified_song_credits_artist_id
    ON verified_song_credits(artist_id);
CREATE INDEX IF NOT EXISTS idx_verified_song_credits_role
    ON verified_song_credits(role);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'artists'
          AND column_name = 'mbid'
    ) THEN
        RAISE EXCEPTION
            'artists.mbid is required by the application. Add/populate it before applying this migration.';
    END IF;
END $$;
