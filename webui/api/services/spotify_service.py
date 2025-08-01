from typing import Annotated
from fastapi import Depends

from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.logging import logger
from api.services.auth_service import AuthService, get_auth_service

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