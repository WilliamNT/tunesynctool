from typing import Annotated, Optional
from fastapi import Depends, HTTPException

from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.service import ServiceCredentialsCreate
from api.core.logging import logger
from api.models.deezer_arl import ARLCreate

class DeezerService:
    """
    Handles operations related to Deezer.
    """

    def __init__(self, auth_service: AuthService, credentials_service: CredentialsService):
        self.auth_service = auth_service
        self.credentials_service = credentials_service

    async def configure_arl(self, arl: ARLCreate, jwt: str) -> None:
        """
        Configures the Deezer ARL cookie for the authenticated user.
        Does not verify the validity of the ARL cookie.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)

        logger.info(f"Configuring Deezer ARL for user {user.id}.")

        credentials = ServiceCredentialsCreate(
            service_name="deezer",
            credentials=self._map_arl_to_dict(arl.arl)
        )

        await self.credentials_service.set_service_credentials(
            user=user,
            credentials=credentials,
        )

    def raise_arl_config_exception(self, message: Optional[str] = None) -> None:
        """
        Raises an HTTPException with a 400 status code and a message indicating that something went wrong while configuring Deezer access.
        """
        
        raise HTTPException(
            status_code=400,
            detail=f"ARL configuration failed: {message}" if message else "ARL configuration failed (unknown reason)",
        )
    
    def _map_arl_to_dict(self, arl: str) -> dict:
        """
        Maps the ARL cookie to a dictionary.
        """
        
        return {
            "arl": arl
        }
    
    def _map_dict_to_arl(self, arl_dict: dict) -> str:
        """
        Maps a dictionary to the ARL cookie.
        """
        
        return arl_dict.get("arl")
    
    async def handle_account_unlink(self, jwt: str) -> None:
        """
        Unlinks the Deezer account from the user.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)

        logger.info(f"Unlinking Deezer account for user {user.id}.")

        await self.credentials_service.delete_credentials(
            user=user,
            service_name="deezer"
        )

def get_deezer_service(auth_service: Annotated[AuthService, Depends(get_auth_service)], credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]) -> DeezerService:
    return DeezerService(
        auth_service=auth_service,
        credentials_service=credentials_service,
    )