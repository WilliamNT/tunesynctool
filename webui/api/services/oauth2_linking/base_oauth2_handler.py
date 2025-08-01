from abc import ABC, abstractmethod
from typing import Any, Optional

from fastapi import HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse

from api.services.providers.base_provider import BaseProvider
from api.services.auth_service import AuthService
from api.core.logging import logger
from api.core.security import verify_oauth2_state
from api.models.service import ServiceCredentialsCreate
from api.models.state import OAuth2State
from api.models.user import User

class BaseOAuth2Handler(ABC):
    def __init__(self, provider: BaseProvider, auth_service: AuthService):
        self.auth_service = auth_service
        self.provider = provider

    @abstractmethod
    async def prepare_authorization_url(self, state: str) -> str:
        """
        Abstract method. Should return the OAuth2 authorization page URL, with the state and all necessary parameters included.
        """

        pass

    async def request_user_authorization(self, state: str) -> RedirectResponse:
        """
        Initiates the authorization process.

        Redirects the user to the authorization page.
        The user will be asked to log in and authorize the application.
        """

        user = await self.auth_service.resolve_user_from_oauth2_state(
            state=state,
            provider_name=self.provider.provider_name
        )

        redirect_url = await self.prepare_authorization_url(state)

        logger.info(f"Initiating {self.provider.provider_name} authorization flow. Redirecting user {user.id} to the provider to request access.")

        return RedirectResponse(
            url=redirect_url,
            status_code=302,
        )
    
    async def handle_authorization_callback(self, state: str, code: Optional[str] = None, error: Optional[str] = None) -> HTMLResponse | RedirectResponse:
        logger.info(f"Received OAuth2 callback from {self.provider.provider_name}.")
        
        decoded_state = self._decode_state(state)

        early_redirect = self._handle_callback_error(error, decoded_state)
        if early_redirect:
            return early_redirect

        if not code:
            logger.error(f"Rejecting {self.provider.provider_name} callback. No code was returned.")
            self._raise_flow_exception("Invalid code")

        user = await self.auth_service.resolve_user_from_oauth2_state(
            state=state,
            provider_name=self.provider.provider_name
        )

        token_details = await self.exchange_code_for_token(code, user, state)
        new_credentials = ServiceCredentialsCreate(
            service_name=self.provider.provider_name,
            credentials=token_details
        )

        await self.provider.set_credentials(
            credentials=new_credentials,
            user=user
        )

        return RedirectResponse(
            url=decoded_state.redirect_uri,
            status_code=status.HTTP_302_FOUND
        )

    @abstractmethod
    async def exchange_code_for_token(self, code: str, user: User, state: str) -> dict:
        """
        Abstract method. Takes care of the exchange of the provider response code for a token.
        """
        
        pass

    def _decode_state(self, state: Optional[str]) -> OAuth2State:
        if not state:
            logger.error(f"Rejecting {self.provider.provider_name} callback: {self.provider.provider_name} didn't return the state.")
            self._raise_flow_exception("Invalid state")

        decoded_state = verify_oauth2_state(
            state=state,
            provider_name=self.provider.provider_name
        )

        if not decoded_state:
            logger.error(f"Rejecting {self.provider.provider_name} callback: {self.provider.provider_name} returned a malformed state.")
            self._raise_flow_exception("Invalid state")

        return decoded_state
    
    def _raise_flow_exception(self, message: Optional[str] = None) -> None:
        """
        Raises an HTTPException with a 400 status code and a message indicating that the Google authorization flow failed.
        """
        
        raise HTTPException(
            status_code=400,
            detail=f"Flow failed: {message}" if message else "Flow failed (unknown reason)",
        )
    
    def _handle_callback_error(self, error: Optional[str], decoded_state: OAuth2State) -> Optional[RedirectResponse]:
        if error:
            logger.warning(f"Google authorization flow failed. Google said: \"{error}\".")

            return RedirectResponse(
                url=decoded_state.redirect_uri,
                status_code=status.HTTP_302_FOUND
            )