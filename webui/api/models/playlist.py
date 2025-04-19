from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from .entity import EntityMetaRead, EntitySingleAuthorRead, EntityIdentifiersBase

class PlaylistRead(BaseModel):
    """
    Represents a playlist.
    """

    title: str = Field(description="Title of the playlist.")
    description: Optional[str] = Field(default=None, description="Description of the playlist (if available).")
    is_public: bool = Field(description="Indicates if the playlist is public.")    
    
    author: EntitySingleAuthorRead = Field(description="Author of the playlist.")
    meta: EntityMetaRead = Field(description="Meta information of the track.")
    identifiers: EntityIdentifiersBase = Field(description="Identifiers of the playlist.")

    @field_validator("description")
    @classmethod
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    
class PlaylistCreate(BaseModel):
    """
    Information required to create a new playlist.
    """

    title: str = Field(description="Title of the playlist. Cannot be an empty string.")

    @field_validator("title", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    
class PlaylistMultiTrackInsert(BaseModel):
    """
    Information required to insert a track into a playlist.
    """

    provider_ids: List[str] = Field(description="ID of the track to be inserted. Cannot be an empty string.")

    @field_validator("provider_ids", mode="before")
    @classmethod
    def provider_ids_validator(cls, v):
        if len(v) == 0:
            raise ValueError("provider_ids cannot be an empty list.")
        
        for provider_id in v:
            if isinstance(provider_id, str) and provider_id.strip() == "":
                raise ValueError("provider_ids cannot contain empty strings.")
            
        v = list(set(v))

        return v