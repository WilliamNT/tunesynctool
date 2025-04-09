from typing import Annotated, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.core.database import get_session
from api.models.user import User
from api.models.service import ServiceCredentials, ServiceCredentialsCreate
from api.helpers.database import create

class CredentialsService:
    """
    Service for managing credentials.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_service_credentials(self, user: User, service_name: str) -> Optional[ServiceCredentials]:
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
            existing_credentials.credentials = credentials.credentials

            self.db.add(existing_credentials)
            await self.db.commit()

            return existing_credentials
        
        new_credentials = ServiceCredentials(
            user_id=user.id,
            service_name=credentials.service_name,
        )

        new_credentials.credentials = credentials.credentials

        return await create(
            session=self.db,
            obj=new_credentials,
        )

def get_credentials_service(db: Annotated[AsyncSession, Depends(get_session)]) -> CredentialsService:
    return CredentialsService(db)