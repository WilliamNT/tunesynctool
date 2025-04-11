from datetime import timedelta

from pydantic import BaseModel, Field

class AccessToken(BaseModel):
    """
    Represents an access token.
    """

    access_token: str = Field(description="The access token.")

    token_type: str = Field(description="The type of token.")

    expires_in: int = Field(description="The expiration time in seconds.")