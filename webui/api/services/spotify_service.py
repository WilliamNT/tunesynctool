from typing import Annotated, Optional
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import Depends, HTTPException, Response, status
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler
from spotipy.exceptions import SpotifyOauthError

from api.core.config import config
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.service import ServiceCredentialsCreate
from api.models.user import User
from api.core.logging import logger
from api.core.security import generate_oauth2_state, verify_oauth2_state
from api.services.user_service import UserService, get_user_service
from api.services.auth_service import AuthService, get_auth_service
from api.models.state import OAuth2State

class SpotifyService:
    """
    Handles operations related to Spotify.
    """

    def __init__(self, auth_service: AuthService, credentials_service: CredentialsService):
        self.auth_service = auth_service
        self.credentials_service = credentials_service

    async def handle_account_unlink(self, jwt: str) -> None:
        """
        Unlinks the Spotify account from the user.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)

        logger.info(f"Unlinking Spotify account for user {user.id}.")

        await self.credentials_service.delete_credentials(
            user=user,
            service_name="spotify"
        )

def get_spotify_service(auth_service: Annotated[AuthService, Depends(get_auth_service)], credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]) -> SpotifyService:
    """
    Returns an instance of the SpotifyService.
    """
    
    return SpotifyService(
        credentials_service=credentials_service,
        auth_service=auth_service
    )