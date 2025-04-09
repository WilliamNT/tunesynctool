from typing import Annotated
from fastapi.responses import RedirectResponse
from fastapi import Depends, HTTPException, status
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler
import asyncio

from api.core.config import config
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.service import ServiceCredentialsCreate
from api.models.user import User

class _CustomCacheHandler(CacheHandler):
    """
    We override the default cache handler to avoid using a file-based cache.
    """

    def __init__(self, credentials_service: CredentialsService, user: User):
        self.credentials_service = credentials_service
        self.user = user
        super().__init__()

    def get_cached_token(self):
        loop = asyncio.get_event_loop()
        return asyncio.run_coroutine_threadsafe(self.credentials_service.get_service_credentials(
            user=self.user,
            service_name="spotify",
        ), loop)
    
    def save_token_to_cache(self, token_info):
        loop = asyncio.get_event_loop()
        return asyncio.run_coroutine_threadsafe(self.credentials_service.set_service_credentials(
            user=self.user,
            credentials=token_info
        ), loop)

class SpotifyService:
    """
    Handles operations related to Spotify.
    """

    def __init__(self, auth_service: AuthService, credentials_service: CredentialsService):
        self.auth_service = auth_service
        self.credentials_service = credentials_service

    def _get_spotify_oauth2(self, user: User) -> SpotifyOAuth:
        return SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI,
            scope=config.SPOTIFY_SCOPES,
            show_dialog=True,
            cache_handler=_CustomCacheHandler(
                credentials_service=self.credentials_service,
                user=user,
            ),
        )

    async def request_user_authorization(self, jwt: str) -> RedirectResponse:
        """
        Initiates the Spotify login process.

        We first have to request user authorization to access their Spotify account.
        This is done by redirecting the user to the Spotify authorization page.
        """

        spotify_oauth2 = self._get_spotify_oauth2(
            user=await self.auth_service.resolve_user_from_jwt(jwt)
        )

        return RedirectResponse(
            url=spotify_oauth2.get_authorize_url(),
            status_code=status.HTTP_302_FOUND
        )
    
    async def handle_authorization_callback(self, code: str, jwt: str) -> None:
        """
        Handles the callback from Spotify after the user has granted authorization.
        
        This method exchanges the authorization code for an access token.
        """
        
        user = await self.auth_service.resolve_user_from_jwt(jwt)

        token_details: dict = self._get_spotify_oauth2(user).get_access_token(
            code=code,
            check_cache=False,
            as_dict=True
        )

        if not token_details:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization code",
            )
        
        credentials = ServiceCredentialsCreate(
            service_name="spotify",
            credentials=token_details
        )

        await self.credentials_service.set_service_credentials(
            user=user,
            credentials=credentials
        )
    
def get_spotify_service(auth_service: Annotated[AuthService, Depends(get_auth_service)], credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]) -> SpotifyService:
    """
    Returns an instance of the SpotifyService.
    """
    
    return SpotifyService(
        auth_service=auth_service,
        credentials_service=credentials_service,
    )