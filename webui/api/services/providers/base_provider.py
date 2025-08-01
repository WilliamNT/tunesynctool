from typing import Optional

from api.services.credentials_service import CredentialsService
from api.models.service import ServiceCredentials, ServiceCredentialsCreate
from api.models.user import User

class BaseProvider:
    def __init__(self, credentials_service: CredentialsService, provider_name: str):
        self.credentials_service = credentials_service
        self.provider_name = provider_name

    async def get_credentials(self, user: User) -> Optional[ServiceCredentials]:
        """
        Retrieves credentials for the given provider and user.
        """

        return await self.credentials_service.get_service_credentials(
            user=user,
            service_name=self.provider_name
        )

    async def set_credentials(self, credentials: ServiceCredentialsCreate, user: User) -> ServiceCredentials:
        """
        Saves new credentials, **or overwrites them if they already exist** for the specified user and provider.
        """

        if credentials.service_name != self.provider_name:
            raise ValueError(f"Provider \"{self.provider_name}\" can only set credentials for its own kind, not \"{credentials.service_name}\". Did you pass the wrong variable?")

        return await self.credentials_service.set_service_credentials(
            user=user,
            credentials=credentials
        )
    
    async def delete_credentials(self, provider_name: str, user: User, log_reason: Optional[str] = None) -> None:
        """
        Deletes the credentials for the given user and provider.
        Can be safely called even if the credentials don't exist.
        """
        
        await self.credentials_service.delete_credentials(
            user=user,
            service_name=provider_name,
            log_reason=log_reason
        )