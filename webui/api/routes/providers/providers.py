from typing import Annotated
from fastapi import APIRouter, Depends

from api.models.service import ProviderState
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.security import oauth2_scheme
from api.helpers.service_driver import DRIVERS
from api.models.collection import Collection

router = APIRouter(
    prefix="/providers",
    tags=["Providers"],
)

@router.get(
    path="/connected",
    summary="Get the list of all connected providers",
    operation_id="getConnectedProviders",
)
async def providers(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> Collection[ProviderState]:
    """
    Get the list of all **connected** providers.
    """
    
    user = await auth_service.resolve_user_from_jwt(jwt)
    return await credentials_service.get_states_of_all_connected_providers(user)

@router.get(
    path="",
    summary="Get the list of all accepted provider names",
    operation_id="getValidProviderNames",
)
async def valid_providers() -> list[str]:
    """
    Returns a list of all accepted provider names that clients can set in the `?provider=` query parameter across endpoints.

    An example use of this endpoint would be to populate a dropdown list in the client UI in a search field.
    """

    return list(DRIVERS.keys())