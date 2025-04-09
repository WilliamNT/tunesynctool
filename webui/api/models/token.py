from datetime import datetime

class Token:
    """
    Represents a token model.
    """

    value: str
    """The JWT itself."""

    expires_at: datetime
    """The expiration date of the token."""