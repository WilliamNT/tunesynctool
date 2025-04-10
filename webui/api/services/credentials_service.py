from typing import Annotated, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.core.database import get_session
from api.models.user import User
from api.models.service import ProviderState, ServiceCredentials, ServiceCredentialsCreate
from api.helpers.database import create, update
from api.core.logging import logger

class CredentialsService:
    """
    Service for managing credentials.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_service_credentials(self, user: User, service_name: str) -> Optional[ServiceCredentials]:
        logger.info(f"Accessing credentials for user {user.id} and service \"{service_name}\".")

        result = await self.db.execute(
            select(ServiceCredentials).where(
                ServiceCredentials.user_id == user.id,
                ServiceCredentials.service_name == service_name,
            )
        )

        return result.scalar_one_or_none()

    async def set_service_credentials(self, user: User, credentials: ServiceCredentialsCreate) -> ServiceCredentials:
        """
        Sets the credentials for the user for the service.
        
        :param user: The user to set the credentials for.
        :param credentials: The service credentials to set.
        """
        
        existing_credentials = await self.get_service_credentials(
            user=user,
            service_name=credentials.service_name,
        )

        if existing_credentials:
            return await self._update_credentials(
                user_id=user.id,
                current_credentials=existing_credentials,
                new_credentials=credentials
            )
        
        return await self._save_new_credentials(
            user_id=user.id,
            credentials_to_save=credentials
        )
    
    async def _update_credentials(self, user_id: int, current_credentials: ServiceCredentials, new_credentials: ServiceCredentialsCreate) -> ServiceCredentials:
        """
        Updates the credentials for the user and service.

        :param user_id: The ID of the user to update the credentials for.
        :param current_credentials: The current credentials for the user and service.
        :param new_credentials: The new service credentials to set.
        :return: The updated credentials.
        """
        
        current_credentials.credentials = new_credentials.credentials

        logger.info(f"Updating credentials for user {user_id} and service \"{new_credentials.service_name}\".")

        return await update(
            session=self.db,
            obj=current_credentials,
        )
    
    async def _save_new_credentials(self, user_id: int, credentials_to_save: ServiceCredentialsCreate) -> ServiceCredentials:
        """
        Saves new credentials for the user and service.
        
        :param user_id: The ID of the user to save the credentials for.
        :param credentials_to_save: The service credentials to save.
        :return: The saved credentials.
        """
        
        new_credentials = ServiceCredentials(
            user_id=user_id,
            service_name=credentials_to_save.service_name,
        )

        new_credentials.credentials = credentials_to_save.credentials

        logger.info(f"Creating credentials for user {user_id} and service \"{credentials_to_save.service_name}\".")

        return await create(
            session=self.db,
            obj=new_credentials,
        )
    
    async def get_provider_state(self, user: User, service_name: str) -> ProviderState:
        credentials = await self.get_service_credentials(
            user=user,
            service_name=service_name,
        )

        return ProviderState(
            provider_name=service_name,
            is_connected=credentials is not None,
        )

def get_credentials_service(db: Annotated[AsyncSession, Depends(get_session)]) -> CredentialsService:
    return CredentialsService(db)