from pydantic import BaseModel

class ARLCreate(BaseModel):
    """
    Represents the ARL cookie.
    """

    arl: str