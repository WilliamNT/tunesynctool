from pydantic import BaseModel, Field

class SubsonicCredentials(BaseModel):
    """
    Represents the Subsonic credentials.
    """

    username: str = Field(description="The Subsonic username.")
    password: str = Field(description="The Subsonic password.")