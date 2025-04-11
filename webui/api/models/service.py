from sqlmodel import SQLModel, Field, Text, Column
from pydantic import BaseModel

from api.helpers.encryption import encrypt_dict, decrypt_dict

class ServiceCredentials(SQLModel, table=True):
    """
    Represents credentials for a service.
    """

    __tablename__ = "service_credentials"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    service_name: str = Field(max_length=255, nullable=False)
    encrypted_credentials: str = Field(nullable=False, sa_type=Text)

    @property
    def credentials(self) -> dict:
        """
        Get the decrypted credentials.
        """

        return decrypt_dict(self.encrypted_credentials)
    
    @credentials.setter
    def credentials(self, value: dict):
        """
        Encrypts and sets the credentials.
        """

        self.encrypted_credentials = encrypt_dict(value)

class ServiceCredentialsCreate(BaseModel):
    """
    Represents the data required to save service credentials.
    """

    service_name: str = Field(max_length=255, nullable=False)
    credentials: dict = Field(nullable=False)

class ProviderState(BaseModel):
    """
    Represents the state of a provider.
    """

    provider_name: str = Field(description="The name of the provider.")
    is_connected: bool = Field(description="Whether the provider is connected (linked) to the authenticated user.")