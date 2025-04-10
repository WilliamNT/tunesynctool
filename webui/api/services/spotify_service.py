from typing import Annotated, Optional
from fastapi.responses import RedirectResponse
from fastapi import Depends, HTTPException, status
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler
from spotipy.exceptions import SpotifyOauthError
import asyncio

from api.core.config import config
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.service import ServiceCredentialsCreate
from api.models.user import User
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
            cache_handler=_FakeCacheHandler(),
        )

    async def request_user_authorization(self, jwt: str) -> RedirectResponse:
        """
        Initiates the Spotify login process.

        We first have to request user authorization to access their Spotify account.
        This is done by redirecting the user to the Spotify authorization page.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)
        
        spotify_oauth2 = self._get_spotify_oauth2(
            user=user
        )

        logger.info(f"Initiating Spotify authorization code flow. Redirecting user {user.id} to Spotify to request access.")

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

        try:
            logger.info(f"Received Spotify callback. User {user.id} has granted access.")

            token_details: dict = self._get_spotify_oauth2(user).get_access_token(
                code=code,
                check_cache=False,
                as_dict=True
            )

            if not token_details:
                self.raise_flow_exception()
        except SpotifyOauthError as e:
            logger.error(f"Spotify authorization flow failed. Spotify said: \"{e.error_description}\".")
            self.raise_flow_exception(e.error_description)
        
        credentials = ServiceCredentialsCreate(
            service_name="spotify",
            credentials=token_details
        )

        await self.credentials_service.set_service_credentials(
            user=user,
            credentials=credentials
        )

    def raise_flow_exception(self, message: Optional[str] = None) -> None:
        """
        Raises an HTTPException with a 400 status code and a message indicating that the Spotify authorization flow failed.
        """
        
        raise HTTPException(
            status_code=400,
            detail=f"Flow failed: {message}" if message else "Flow failed (unknown reason)",
        )    
    
def get_spotify_service(auth_service: Annotated[AuthService, Depends(get_auth_service)], credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]) -> SpotifyService:
    """
    Returns an instance of the SpotifyService.
    """
    
    return SpotifyService(
        auth_service=auth_service,
        credentials_service=credentials_service,
    )