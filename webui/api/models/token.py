from datetime import datetime
from pydantic import BaseModel

class Token(BaseModel):
    """
    Represents a token model.
    """

    value: str
    """The JWT itself."""

    expires_at: datetime
    """The expiration date of the token."""