from pydantic import BaseModel, Field, AnyUrl
from typing import Optional

from .search import SearchParamsBase

class OAuth2StateBase(BaseModel):
    """
    Base model for OAuth2 state.
    """
    
    redirect_uri: AnyUrl = Field(description="The redirect URI specified by the client.")

class OAuth2State(SearchParamsBase, OAuth2StateBase):
    """
    OAuth2 state model to validate the flow and restore client state.
    """
    
    user_id: int = Field(description="The ID of the user.")

class OAuth2StateCreate(OAuth2StateBase):
    """
    Data to create a new OAuth2 state.
    """