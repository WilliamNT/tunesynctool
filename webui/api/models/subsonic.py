from pydantic import BaseModel

class SubsonicCredentials(BaseModel):
    """
    Represents the Subsonic credentials.
    """

    username: str
    password: str