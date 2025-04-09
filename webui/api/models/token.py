from datetime import timedelta

from pydantic import BaseModel

class AccessToken(BaseModel):
    """
    Represents an access token.
    """

    access_token: str
    """The JWT itself."""

    token_type: str
    """The expiration date of the token."""

    expires_in: int
    """The expiration date of the token."""