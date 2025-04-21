from typing import Optional
from pydantic import BaseModel, Field

class EntityMetaRead(BaseModel):
    """
    Represents meta information of an entity.
    """

    provider_name: str = Field(description="Name of the provider.")

class EntitySingleAuthorRead(BaseModel):
    """
    Represents the author of an entity.
    """

    primary: Optional[str] = Field(description="Name of the primary author.", default=None)

class EntityMultiAuthorRead(EntitySingleAuthorRead):
    """
    Represents authors of an entity.
    """

    collaborating: list[str] = Field(default=[], description="List of additional artists. If none are known, an empty list.")

class EntityIdentifiersBase(BaseModel):
    """
    Base class for identifiers of an entity.
    """

    provider_id: str = Field(description="ID of the entity in the provider's database.")