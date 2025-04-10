from typing import Annotated

from fastapi import Depends
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.logging import logger
from api.models.subsonic import SubsonicCredentials
from api.models.service import ServiceCredentialsCreate

class SubsonicService:
    """
    Handles operations related to Subsonic.
    """

    def __init__(self, auth_service: AuthService, credentials_service: CredentialsService):
        self.auth_service = auth_service
        self.credentials_service = credentials_service

    async def configure_credentials(self, credentials: SubsonicCredentials, jwt: str) -> None:
        """
        Configures the Subsonic credentials for the authenticated user.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)

        logger.info(f"Configuring Subsonic credentials for user {user.id}.")

        service_credentials = ServiceCredentialsCreate(
            service_name="subsonic",
            credentials=self._map_credentials_to_dict(credentials)
        )

        await self.credentials_service.set_service_credentials(
            user=user,
            credentials=service_credentials,
        )

    def _map_credentials_to_dict(self, credentials: SubsonicCredentials) -> dict:
        """
        Maps the Subsonic credentials to a dictionary.
        
        :param credentials: The Subsonic credentials to map.
        :return: A dictionary representation of the Subsonic credentials.
        """
        
        return {
            "username": credentials.username,
            "password": credentials.password
        }
    
    def _map_dict_to_credentials(self, cred_dict: dict) -> SubsonicCredentials:
        """
        Maps a dictionary to Subsonic credentials.

        :param cred_dict: The dictionary to map.
        :return: A SubsonicCredentials object.
        """
        
        return SubsonicCredentials(
            username=cred_dict["username"],
            password=cred_dict["password"]
        )

    async def handle_account_unlink(self, jwt: str) -> None:
        """
        Unlinks the Subsonic account from the user.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)

        logger.info(f"Unlinking Subsonic account for user {user.id}.")

        await self.credentials_service.delete_credentials(
            user=user,
            service_name="subsonic"
        )

def get_subsonic_service(auth_service: Annotated[AuthService, Depends(get_auth_service)], credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]) -> SubsonicService:    
    return SubsonicService(
        auth_service=auth_service,
        credentials_service=credentials_service,
    )