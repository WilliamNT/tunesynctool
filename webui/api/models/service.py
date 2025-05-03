from typing import Optional
from sqlmodel import SQLModel, Field, Text
from pydantic import BaseModel
from enum import Enum

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

class ProviderLinkType(Enum):
    """
    Represents the type of link for a provider.
    """

    OAUTH2 = "oauth2"
    FORM = "form"

class ProviderLinkingRead(BaseModel):
    link_type: ProviderLinkType = Field(description="The type of linking the user has to go through for the provider.")
    target_url: str = Field(description="Relevant URL for OAuth2 flow or form submission.")

class ProviderAboutRead(BaseModel):
    """
    Generic, UI display information about a provider.
    """

    description: str = Field(description="A description of the provider meant to be used in user facing interfaces.")
    display_name: str = Field(description="The name of the provider meant to be used in user facing interfaces.")
    favicon: str = Field(description="The URL to the favicon of the provider.")

class ProviderRead(BaseModel):
    """
    Generic, UI display information about a provider.
    """

    provider_name: str = Field(description="The name of the provider.")
    is_configured: bool = Field(description="Whether the provider was configured.")
    linking: ProviderLinkingRead = Field(description="Information about the linking process for the provider.")
    ui: ProviderAboutRead = Field(description="The UI display information about the provider.")