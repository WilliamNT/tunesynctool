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

    def _get_spotify_oauth2(self, state: str) -> SpotifyOAuth:
        return SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI,
            scope=config.SPOTIFY_SCOPES,
            show_dialog=True,
            cache_handler=_FakeCacheHandler(),
            state=state
        )

    async def request_user_authorization(self, state: str) -> RedirectResponse:
        """
        Initiates the Spotify login process.

        We first have to request user authorization to access their Spotify account.
        This is done by redirecting the user to the Spotify authorization page.
        """

        user = await self.auth_service.resolve_user_from_oauth2_state(
            state=state,
            provider_name="spotify"
        )
        
        spotify_oauth2 = self._get_spotify_oauth2(
            state=state
        )

        logger.info(f"Initiating Spotify authorization code flow. Redirecting user {user.id} to Spotify to request access.")

        return RedirectResponse(
            url=spotify_oauth2.get_authorize_url(),
            status_code=status.HTTP_302_FOUND
        )
    
    async def handle_authorization_callback(self, state: str, code: Optional[str] = None, error: Optional[str] = None) -> HTMLResponse | RedirectResponse:
        """
        Handles the callback from Spotify after the user has granted authorization.
        
        This method exchanges the authorization code for an access token.
        """
        
        decoded_state = self._decode_state(state)

        redirect_early = self._handle_callback_error(error=error, decoded_state=decoded_state)
        if redirect_early:
            return redirect_early
                
        if not code:
            logger.error("Rejecting Spotify callback. No code provided.")
            self.raise_flow_exception("Invalid code")

        user = await self.auth_service.resolve_user_from_oauth2_state(state=state, provider_name="spotify")

        token_details = self._exchange_callback_code_for_token(code=code, user=user, state=state)  
        new_credentials = ServiceCredentialsCreate(service_name="spotify", credentials=token_details)
        await self.credentials_service.set_service_credentials(user=user, credentials=new_credentials)
    
        return RedirectResponse(url=decoded_state.redirect_uri, status_code=status.HTTP_302_FOUND)
    
    def _decode_state(self, state: Optional[str]) -> OAuth2State:
        if not state:
            logger.error("Rejecting Spotify callback. Spotify didn't return the state.")
            self.raise_flow_exception("Invalid state")

        decoded_state = verify_oauth2_state(
            state=state,
            provider_name="spotify"
        )
        
        if not decoded_state:
            logger.error("Rejecting Spotify callback. Invalid state.")
            self.raise_flow_exception("Invalid state")

        return decoded_state
    
    def _handle_callback_error(self, error: Optional[str], decoded_state: OAuth2State) -> Optional[RedirectResponse]:
        if error:
            logger.warning(f"Spotify authorization flow failed. Spotify said: \"{error}\".")

            return RedirectResponse(
                url=decoded_state.redirect_uri,
                status_code=status.HTTP_302_FOUND
            )
        
    def _exchange_callback_code_for_token(self, code: str, user: User, state: str) -> dict:
        try:
            logger.info(f"Received Spotify callback. User {user.id} has likely granted access.")

            token_details: dict = self._get_spotify_oauth2(state).get_access_token(
                code=code,
                check_cache=False,
                as_dict=True
            )

            if not token_details:
                logger.error("Failed to decode Spotify token details.")
                self.raise_flow_exception()

            return token_details
        except SpotifyOauthError as e:
            logger.error(f"Spotify authorization flow failed. Spotify said: \"{e.error_description}\".")
            self.raise_flow_exception(e.error_description)

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
        credentials_service=credentials_service,
        auth_service=auth_service
    )