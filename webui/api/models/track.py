from typing import Optional
from pydantic import BaseModel, Field, field_validator

from .entity import EntityMetaRead, EntityMultiAuthorRead, EntityIdentifiersBase
    
class TrackIdentifiersThirdPartyBase(BaseModel):
    """
    Represents common third-party identifiers of a track.
    """

    isrc: Optional[str] = Field(default=None, description="International Standard Recording Code (if available).")
    musicbrainz: Optional[str] = Field(default=None, description="MusicBrainz ID (if available).")

    @field_validator("isrc")
    @classmethod
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    
    @field_validator("musicbrainz")
    @classmethod
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v    

class TrackIdentifiersRead(EntityIdentifiersBase, TrackIdentifiersThirdPartyBase):
    """
    Represents identifiers of a track.
    """

class TrackAssetsRead(BaseModel):
    """
    Represents assets of a track.
    """

    cover_image: Optional[str] = Field(default=None, description="Cover image URL (if available).")

class TrackBase(BaseModel):
    """
    Represents common attributes of a track.
    """

    title: str = Field(description="Title of the track.")
    album_name: Optional[str] = Field(description="Name of the album (if available).")
    duration: Optional[int] = Field(default=None, description="Duration of the track in seconds (if available).")
    track_number: Optional[int] = Field(default=None, description="Track number in the album (if available).")
    release_year: Optional[int] = Field(default=None, description="Release year of the track (if available).")

    author: EntityMultiAuthorRead = Field(description="Authors of the track.")
    identifiers: TrackIdentifiersRead = Field(description="Identifiers of the track.")
    assets: TrackAssetsRead = Field(description="Assets of the track.")

class TrackRead(TrackBase):
    """
    Represents a track.
    """
    
    meta: EntityMetaRead = Field(description="Meta information of the track.")

class TrackMatchCreate(TrackBase):
    """
    Metadata that can be used to match a track.
    """

    identifiers: TrackIdentifiersThirdPartyBase = Field(description="Identifiers of the track.")