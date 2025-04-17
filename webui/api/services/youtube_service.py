import json
from typing import Annotated, Optional
from fastapi import Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.config import config
from api.core.logging import logger
from api.models.service import ServiceCredentialsCreate

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

    async def request_user_authorization(self, jwt: str) -> RedirectResponse:
        """
        Initiates the YouTube login process.

        Redirects the user to the YouTube authorization page.
        The user will be asked to log in and authorize the application.

        Details: https://developers.google.com/youtube/v3/quickstart/python
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)

        google_flow = self._get_google_flow()
        authorization_url, state = google_flow.authorization_url(
            access_type="offline",
            include_granted_scopes='true',
            prompt="consent select_account",
        )

        logger.info(f"Initiating Google authorization code flow. Redirecting user {user.id} to Google to request access.")

        return RedirectResponse(
            url=authorization_url,
            status_code=302,
        )
    
    async def handle_authorization_callback(self, callback_url: str, jwt: str) -> None:
        """
        Handles the Google OAuth2 callback after the user has authorized the application.
        
        This method exchanges the authorization code for an access token and stores the credentials.
        """
        user = await self.auth_service.resolve_user_from_jwt(jwt)

        logger.info(f"Received Google callback. User {user.id} has granted access.")

        google_flow = self._get_google_flow()

        try:
            google_flow.fetch_token(
                authorization_response=callback_url
            )
        except OAuth2Error as e:
            logger.error(f"Google authorization flow failed. Google said: \"{e.description}\".")
            self.raise_flow_exception(e.description)

        credentials = ServiceCredentialsCreate(
            service_name="youtube",
            credentials=json.loads(google_flow.credentials.to_json())
        )

        await self.credentials_service.set_service_credentials(
            user=user,
            credentials=credentials
        )

        return HTMLResponse(
            content=f"<h1>Authorization successful!</h1><p>This is a placeholder. Here's some of your info for verification: {credentials.credentials}</p>",
        )

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