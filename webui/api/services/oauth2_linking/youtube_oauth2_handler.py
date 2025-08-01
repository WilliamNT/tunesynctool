import json
from typing import Annotated
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from fastapi import Depends
from api.services.oauth2_linking.base_oauth2_handler import BaseOAuth2Handler
from api.models.user import User
from api.services.auth_service import AuthService, get_auth_service
from api.services.providers.youtube_provider import YouTubeProvider, get_youtube_provider
from api.core.config import config
from api.core.logging import logger

class YouTubeOAuth2Handler(BaseOAuth2Handler):
    def __init__(self, provider, auth_service):
        super().__init__(
            provider=provider,
            auth_service=auth_service
        )

    def _get_flow(self, state: str) -> Flow:
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

    async def prepare_authorization_url(self, state: str) -> str:
        flow = self._get_flow(state)

        url, _state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes='true',
            prompt="consent select_account",
            state=state
        )

        return url

    async def exchange_code_for_token(self, code: str, user: User, state: str) -> dict:
        try:
            flow = self._get_flow(state)
            flow.fetch_token(code=code)

            if not flow.credentials or not flow.credentials.scopes:
                logger.error(f"{self.provider.provider_name} authorization flow failed. No credentials returned or the returned scopes are invalid.")
                self.raise_flow_exception("No credentials returned")

            return json.loads(flow.credentials.to_json())
        except Warning as e:
            if "scope has changed" in str(e).lower():
                logger.warning(f"Rejecting user authorization. User {user.id} granted a different set of scopes than the ones required for all features to properly work.")
                self.raise_flow_exception("Scope mismatch")
            else:
                logger.error(f"Unknown value error in {self.provider.provider_name} code exchange: {e}")
                raise
        except OAuth2Error as e:
            logger.error(f"{self.provider.provider_name} authorization flow failed: {self.provider.provider_name} said: \"{e.description}\".")
            self.raise_flow_exception(e.description)         

def get_youtube_oauth2_handler(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    provider: Annotated[YouTubeProvider, Depends(get_youtube_provider)]
) -> YouTubeOAuth2Handler:
    return YouTubeOAuth2Handler(
        provider=provider,
        auth_service=auth_service
    )