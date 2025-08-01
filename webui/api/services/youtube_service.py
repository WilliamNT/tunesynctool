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

def get_youtube_service(auth_service: Annotated[AuthService, Depends(get_auth_service)], credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]) -> YouTubeService:    
    return YouTubeService(
        auth_service=auth_service,
        credentials_service=credentials_service,
    )