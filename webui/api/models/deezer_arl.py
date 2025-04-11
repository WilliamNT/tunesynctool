from pydantic import BaseModel, Field

class ARLCreate(BaseModel):
    """
    Represents the ARL cookie.
    """

    arl: str = Field(description="The ARL cookie's value.")