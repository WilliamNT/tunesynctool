from typing import Optional
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