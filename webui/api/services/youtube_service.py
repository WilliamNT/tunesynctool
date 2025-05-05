import json
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.config import config
from api.core.logging import logger
from api.models.service import ServiceCredentialsCreate
from api.core.security import verify_oauth2_state
from api.models.state import OAuth2State
from api.models.user import User

"""
To implement the Google OAuth process, I referenced this guide:
https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps
"""

class YouTubeService:
    """
    A service class for handling YouTube-related operations.
    """

    def __init__(self, auth_service: AuthService, credentials_service: CredentialsService):
        self.auth_service = auth_service
        self.credentials_service = credentials_service

    def _get_google_flow(self) -> Flow:
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [config.GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=config.GOOGLE_SCOPES
        )

        flow.redirect_uri = config.GOOGLE_REDIRECT_URI
        return flow

    async def request_user_authorization(self, state: str) -> RedirectResponse:
        """
        Initiates the YouTube login process.

        Redirects the user to the YouTube authorization page.
        The user will be asked to log in and authorize the application.

        Details: https://developers.google.com/youtube/v3/quickstart/python
        """

        user = await self.auth_service.resolve_user_from_oauth2_state(
            state=state,
            provider_name="youtube"
        )

        google_flow = self._get_google_flow()
        authorization_url, state = google_flow.authorization_url(
            access_type="offline",
            include_granted_scopes='true',
            prompt="consent select_account",
            state=state
        )

        logger.info(f"Initiating Google authorization code flow. Redirecting user {user.id} to Google to request access.")

        return RedirectResponse(
            url=authorization_url,
            status_code=302,
        )
    
    async def handle_authorization_callback(self, state: str, code: Optional[str] = None, error: Optional[str] = None) -> HTMLResponse | RedirectResponse:
        """
        Handles the Google OAuth2 callback after the user has authorized the application.
        
        This method exchanges the authorization code for an access token and stores the credentials.
        """
        
        decoded_state = self._decode_state(state)

        redirect_early = self._handle_callback_error(error=error, decoded_state=decoded_state)
        if redirect_early:
            return redirect_early

        if not code:
            logger.error("Rejecting Google callback. No code provided.")
            self.raise_flow_exception("Invalid code")

        user = await self.auth_service.resolve_user_from_oauth2_state(state=state, provider_name="youtube")

        token_details = self._exchange_callback_code_for_token(code=code, user=user)  
        new_credentials = ServiceCredentialsCreate(service_name="youtube", credentials=token_details)
        await self.credentials_service.set_service_credentials(user=user, credentials=new_credentials)

        return RedirectResponse(url=decoded_state.redirect_uri, status_code=status.HTTP_302_FOUND)
    
    def _decode_state(self, state: Optional[str]) -> OAuth2State:
        if not state:
            logger.error("Rejecting Google callback. Google didn't return the state.")
            self.raise_flow_exception("Invalid state")

        decoded_state = verify_oauth2_state(
            state=state,
            provider_name="youtube"
        )
        
        if not decoded_state:
            logger.error("Rejecting Google callback. Invalid state.")
            self.raise_flow_exception("Invalid state")

        return decoded_state
    
    def _handle_callback_error(self, error: Optional[str], decoded_state: OAuth2State) -> Optional[RedirectResponse]:
        if error:
            logger.warning(f"Google authorization flow failed. Google said: \"{error}\".")

            return RedirectResponse(
                url=decoded_state.redirect_uri,
                status_code=status.HTTP_302_FOUND
            )
        
    def _exchange_callback_code_for_token(self, code: str, user: User) -> dict:
        try:
            logger.info(f"Received Google callback. User {user.id} has granted access.")
            
            google_flow = self._get_google_flow()
            google_flow.fetch_token(
                code=code
            )

            if not google_flow.credentials or not google_flow.credentials.scopes:
                logger.error("Google authorization flow failed. No credentials returned or the returned scopes are invalid.")
                self.raise_flow_exception("No credentials returned")

            return json.loads(google_flow.credentials.to_json())
        except Warning as e:
            if "scope has changed" in str(e).lower():
                logger.warning(f"Rejecting user authorization. User {user.id} granted a different set of scopes than the ones required for all features to properly work.")
                self.raise_flow_exception("Scope mismatch")
            else:
                logger.error(f"Unknown value error in Google code exchange: {e}")
                raise
        except OAuth2Error as e:
            logger.error(f"Google authorization flow failed. Google said: \"{e.description}\".")
            self.raise_flow_exception(e.description)

    async def handle_account_unlink(self, jwt: str) -> None:
        """
        Unlinks the Google account from the user.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)

        logger.info(f"Unlinking Google account for user {user.id}.")

        await self.credentials_service.delete_credentials(
            user=user,
            service_name="youtube"
        )

    def raise_flow_exception(self, message: Optional[str] = None) -> None:
        """
        Raises an HTTPException with a 400 status code and a message indicating that the Google authorization flow failed.
        """
        
        raise HTTPException(
            status_code=400,
            detail=f"Flow failed: {message}" if message else "Flow failed (unknown reason)",
        )  

def get_youtube_service(auth_service: Annotated[AuthService, Depends(get_auth_service)], credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]) -> YouTubeService:    
    return YouTubeService(
        auth_service=auth_service,
        credentials_service=credentials_service,
    )