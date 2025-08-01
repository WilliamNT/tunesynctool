from typing import Annotated, Any
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler
from spotipy.exceptions import SpotifyOauthError

from fastapi import Depends
from api.services.oauth2_linking.base_oauth2_handler import BaseOAuth2Handler
from api.models.user import User
from api.services.auth_service import AuthService, get_auth_service
from api.services.providers.spotify_provider import SpotifyProvider, get_spotify_provider
from api.core.config import config
from api.core.logging import logger

class _FakeCacheHandler(CacheHandler):
    """
    We override the default cache handler beause we use our own logic to store the credentials in the database.
    """

    def __init__(self):
        super().__init__()

    async def get_cached_token(self):
        return None
    
    async def save_token_to_cache(self, token_info):
        pass

class SpotifyOAuth2Handler(BaseOAuth2Handler):
    def __init__(self, provider, auth_service):
        super().__init__(
            provider=provider,
            auth_service=auth_service
        )

    def _get_flow(self, state: str) -> SpotifyOAuth:
        return SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI,
            scope=config.SPOTIFY_SCOPES,
            show_dialog=True,
            cache_handler=_FakeCacheHandler(),
            state=state
        )

    async def prepare_authorization_url(self, state: str) -> str:
        flow = self._get_flow(state)
        return flow.get_authorize_url()

    async def exchange_code_for_token(self, code: str, user: User, state: str) -> dict:
        try:        
            token_details: dict = self._get_flow(state).get_access_token(
                code=code,
                check_cache=False,
                as_dict=True
            )

            if not token_details:
                logger.error(f"Failed to exchange {self.provider.provider_name} callback code for token.")
                self._raise_flow_exception()
            
            return token_details
        except SpotifyOauthError as e:
            logger.error(f"{self.provider.provider_name} authorization flow failed: {self.provider.provider_name} said: \"{e.error_description}\".")
            self._raise_flow_exception(e.error_description)

def get_spotify_oauth2_handler(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    provider: Annotated[SpotifyProvider, Depends(get_spotify_provider)]
) -> SpotifyOAuth2Handler:
    return SpotifyOAuth2Handler(
        provider=provider,
        auth_service=auth_service
    )