from typing import Optional
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Index, SQLModel, Field as DBField, JSON, Column
import json

from .entity import EntityMetaRead, EntityMultiAuthorRead, EntityIdentifiersBase, EntityAssetsBase
    
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
    assets: EntityAssetsBase = Field(description="Assets of the track.")

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

class CachedTrack(SQLModel, table=True):
    """
    Represents a cached track.
    """

    __tablename__ = "tracks"
    
    id: Optional[int] = DBField(default=None, primary_key=True)
    title: str = DBField()
    album_name: Optional[str] = DBField()
    duration: Optional[int] = DBField(default=None)
    track_number: Optional[int] = DBField(default=None)
    release_year: Optional[int] = DBField(default=None)
    author: Optional[str] = DBField(default=None)

    isrc: Optional[str] = DBField(default=None)
    musicbrainz: Optional[str] = DBField(default=None)

    collaborators_json: Optional[dict] = DBField(sa_column=Column(JSON))
    """
    Should be treated as a JSON list. Do not use directly. Use `collaborators` instead.
    """
    
    @property
    def collaborators(self) -> list:
        """
        Deserializes the `collaborators_json` JSON into a Python list.

        If something went wrong, an empty list is returned.
        """

        try:
            deserialized = json.loads(self.collaborators_json)
            if isinstance(deserialized, list):
                if all(isinstance(item, str) for item in deserialized):
                    return deserialized
                else:
                    return []
            else:
                return []
        except (json.JSONDecodeError, TypeError):
            return []

    @collaborators.setter
    def collaborators(self, value: Optional[list]):
        """
        Sets and serializes the new value to JSON.
        """

        if value is None:
            self.collaborators_json = json.dumps([])
        elif isinstance(value, list):
            if not all(isinstance(item, str) for item in value):
                raise ValueError("collaborators can only be a list of strings")
            
            self.collaborators_json = json.dumps(value)
        else:
            raise ValueError("collaborators can only be a list or None")

class CachedTrackProviderMapping(SQLModel, table=True):
    """
    A single provider mapping for a cached track.
    """

    __tablename__ = "provider_mappings"
    __table_args__ = (
        Index("idx_provider_provider_id", "provider", "provider_track_id"),
    )

    track_id: int = DBField(foreign_key="tracks.id", primary_key=True)
    provider: str = DBField(max_length=50, primary_key=True)
    provider_track_id: str = DBField(max_length=255, primary_key=True)