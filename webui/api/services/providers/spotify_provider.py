from typing import Annotated

from fastapi import Depends
from api.services.providers.base_provider import BaseProvider
from api.services.credentials_service import CredentialsService, get_credentials_service

class SpotifyProvider(BaseProvider):
    def __init__(self, credentials_service):
        super().__init__(
            credentials_service=credentials_service,
            provider_name="spotify"
        )

def get_spotify_provider(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]
) -> SpotifyProvider:
    return SpotifyProvider(
        credentials_service=credentials_service
    )