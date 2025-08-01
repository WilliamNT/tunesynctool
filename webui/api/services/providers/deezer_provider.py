from typing import Annotated
from fastapi import Depends

from api.services.providers.base_provider import BaseProvider
from api.services.credentials_service import CredentialsService, get_credentials_service

class DeezerProvider(BaseProvider):
    def __init__(self, credentials_service):
        super().__init__(
            credentials_service=credentials_service,
            provider_name="deezer"
        )
    
def get_deezer_provider(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]
) -> DeezerProvider:
    return DeezerProvider(
        credentials_service=credentials_service
    )