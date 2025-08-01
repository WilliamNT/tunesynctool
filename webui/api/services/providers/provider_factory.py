from typing import Annotated
from fastapi import Depends, Query

from api.services.providers.base_provider import BaseProvider
from api.services.providers.spotify_provider import get_spotify_provider
from api.services.providers.youtube_provider import get_youtube_provider
from api.services.providers.deezer_provider import get_deezer_provider
from api.services.providers.subsonic_provider import get_subsonic_provider
from api.services.credentials_service import CredentialsService, get_credentials_service

class ProviderFactory:
    _PROVIDERS = {
        "youtube": get_youtube_provider,
        "spotify": get_spotify_provider,
        "deezer": get_deezer_provider,
        "subsonic": get_subsonic_provider
    }

    @staticmethod
    def create(provider_name: str, credentials_service: CredentialsService) -> BaseProvider:
        result = ProviderFactory._PROVIDERS.get(provider_name)

        if not result:
            raise ValueError(f"ProviderFactory cannot create Provider for \"{provider_name}\" because it doesn't exist. If you implemented a new provider, please update the ProviderFactory so it can support it.")
        
        return result(credentials_service)
    
def get_provider_in_route(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    provider: Annotated[str, Query()],
) -> BaseProvider:
    return ProviderFactory.create(
        provider_name=provider,
        credentials_service=credentials_service
    )