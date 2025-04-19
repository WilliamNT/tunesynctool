from pydantic import BaseModel, Field, field_validator, ValidationError

from api.helpers.service_driver import is_valid_provider, SUPPORTED_PROVIDERS

class SearchParamsBase(BaseModel):
    """
    Base class for search parameters.
    """

    provider: str = Field(description="Name of the provider to search with.")

    @field_validator("provider")
    def normalize_and_validate(cls, v: str) -> str:
        v = v.lower()

        if not is_valid_provider(v):
            raise ValueError(f"provider must be one of: {", ".join(SUPPORTED_PROVIDERS)}")
        
        return v

class SearchParams(SearchParamsBase):
    """
    Search parameters.
    """

    query: str = Field(min_length=3, max_length=100, description="Search query.")
    limit: int = Field(default=5, ge=1, le=10, description="Max numbers of results to return.")
    
class ISRCSearchParams(SearchParamsBase):
    """
    ISRC search parameters.
    """

    isrc: str = Field(min_length=12, max_length=12, description="ISRC (International Standard Recording Code) to search for.")

class LookupByProviderIDParams(SearchParamsBase):
    """
    Track lookup by ID parameters.
    """

    provider_id: str = Field(description="ID of the entity to look up.")

class LookupLibraryPlaylistsParams(SearchParamsBase):
    """
    Lookup playlists saved or owned by a user.
    """

    limit: int = Field(default=10, ge=1, le=25, description="Max numbers of results to return.")