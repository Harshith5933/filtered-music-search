"""Domain models used by the ingestion layer."""

from pydantic import BaseModel, Field


class Artist(BaseModel):
    mbid: str
    name: str


class Release(BaseModel):
    mbid: str
    title: str
    date: str | None = None


class Song(BaseModel):
    recording_mbid: str
    work_mbid: str | None = None
    title: str
    credited_artists: list[Artist] = Field(default_factory=list)
    singers: list[Artist] = Field(default_factory=list)
    composers: list[Artist] = Field(default_factory=list)
    lyricists: list[Artist] = Field(default_factory=list)
    releases: list[Release] = Field(default_factory=list)
