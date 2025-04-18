from typing import Annotated, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from google.oauth2.credentials import Credentials as GoogleCredentials
from google.auth.credentials import TokenState as GoogleTokenState
from google.auth.transport.requests import Request as GoogleTokenRequest
import json

from api.core.database import get_session
from api.models.user import User
from api.models.service import ProviderState, ServiceCredentials, ServiceCredentialsCreate
from api.helpers.database import create, update, delete
from api.core.logging import logger
from api.core.config import config

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

        if current_credentials.service_name != new_credentials.service_name:
            raise ValueError(f"Service name mismatch: {current_credentials.service_name} != {new_credentials.service_name}. Did you mix up the update and create methods?")
        
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
        """
        Returns the state of the provider for the user.
        
        :param user: The user to get the provider state for.
        :param service_name: The name of the service to get the provider state for.
        :return: The provider state.
        """

        credentials = await self.get_service_credentials(
            user=user,
            service_name=service_name,
        )

        return ProviderState(
            provider_name=service_name,
            is_connected=credentials is not None,
        )
    
    
    async def delete_credentials(self, user: User, service_name: str) -> None:
        """
        Permanently deletes the credentials for the user and service.

        :param user: The user to delete the credentials for.
        :param service_name: The name of the service to delete the credentials for.
        :return: None
        """

        credentials = await self.get_service_credentials(
            user=user,
            service_name=service_name,
        )

        if not credentials:
            logger.warning(f"Credentials for user {user.id} and service \"{service_name}\" don't exist but their deletion was requested anyway.")
            return
        
        logger.info(f"Deleting credentials for user {user.id} and service \"{service_name}\".")

        await delete(
            session=self.db,
            obj=credentials,
        )

    async def get_states_of_all_connected_providers(self, user: User) -> list[ProviderState]:
        """
        Returns the list of all **connected** providers for the user.

        :param user: The user to get the connected providers for.
        :return: The list of connected providers.
        """

        logger.info(f"Getting all connected providers for user {user.id}.")

        result = await self.db.execute(
            select(ServiceCredentials).where(
                ServiceCredentials.user_id == user.id,
            )
        )

        credentials = []
        for row in result.scalars().all():
            credentials.append(
                ProviderState(
                    provider_name=row.service_name,
                    is_connected=True,
                )
            )

        return credentials
    
    async def refresh_google_credentials(self, user: User, credentials: ServiceCredentials) -> ServiceCredentials:
        """
        Refreshes the Google credentials for the user **if needed**.

        :param user: The user to refresh the credentials for.
        :param credentials: The service credentials to refresh.
        :return: The refreshed credentials.
        :raises ValueError: If the credentials are somehow invalid.
        """

        if credentials.service_name != "youtube":
            raise ValueError(f"Cannot refresh credentials for service \"{credentials.service_name}\". This method only supports Google services.")

        google_credentials = GoogleCredentials.from_authorized_user_info(
            info=json.loads(credentials.credentials),
            scopes=config.GOOGLE_SCOPES
        )

        if google_credentials.token_state == GoogleTokenState.FRESH:
            logger.debug(f"Google credentials for user {user.id} are already fresh. No need to refresh.")
            return credentials
        
        if not google_credentials.refresh_token:
            logger.error(f"Google credentials for user {user.id} are not fresh and do not have a refresh token. Cannot refresh.")
            raise ValueError(f"Cannot refresh Google credentials because they are missing a refresh token. This is likely a bug with the Google library.")
        
        logger.debug(f"Refreshing Google credentials for user {user.id}.")
        google_credentials.refresh(GoogleTokenRequest())

        fresh_credentials = await self._update_credentials(
            user_id=user.id,
            current_credentials=credentials,
            new_credentials=ServiceCredentialsCreate(
                service_name=credentials.service_name,
                credentials=json.loads(google_credentials.to_json())
            )
        )

        return fresh_credentials

def get_credentials_service(db: Annotated[AsyncSession, Depends(get_session)]) -> CredentialsService:
    return CredentialsService(db)