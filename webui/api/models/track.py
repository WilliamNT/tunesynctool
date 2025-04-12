from typing import Optional
from pydantic import BaseModel, Field

class TrackMetaRead(BaseModel):
    """
    Represents meta information of a track.
    """

    provider_name: str = Field(description="Name of the provider.")

class TrackIdentifiersRead(BaseModel):
    """
    Represents identifiers of a track.
    """

    provider_id: str = Field(description="ID of the track in the provider's database.")
    isrc: Optional[str] = Field(default=None, description="International Standard Recording Code (if available).")
    musicbrainz: Optional[str] = Field(default=None, description="MusicBrainz ID (if available).")

class TrackArtistsRead(BaseModel):
    """
    Represents artists of a track.
    """

    primary: str = Field(description="Name of the primary artist.")
    collaborating: list[str] = Field(default=[], description="List of additional artists. If none are known, an empty list.")

class TrackRead(BaseModel):
    """
    Represents a track.
    """

    title: str = Field(description="Title of the track.")
    album_name: Optional[str] = Field(description="Name of the album (if available).")
    duration: Optional[int] = Field(default=None, description="Duration of the track in seconds (if available).")
    track_number: Optional[int] = Field(default=None, description="Track number in the album (if available).")
    release_year: Optional[int] = Field(default=None, description="Release year of the track (if available).")
    artists: TrackArtistsRead = Field(description="Artists of the track.")
    meta: TrackMetaRead = Field(description="Meta information of the track.")
    identifiers: TrackIdentifiersRead = Field(description="Identifiers of the track.")