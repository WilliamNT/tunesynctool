from pydantic import BaseModel, Field, field_validator, ValidationError

from api.helpers.service_driver import is_valid_provider, SUPPORTED_PROVIDERS

class SearchParams(BaseModel):
    """
    Search parameters.
    """

    provider: str = Field(description="Name of the provider to search with.")
    query: str = Field(min_length=3, max_length=100, description="Search query.")
    limit: int = Field(default=5, ge=1, le=10, description="Max numbers of results to return.")

    @field_validator("provider")
    def normalize_and_validate(cls, v: str) -> str:
        v = v.lower()

        if not is_valid_provider(v):
            raise ValueError(f"provider must be one of: {", ".join(SUPPORTED_PROVIDERS)}")
        
        return v