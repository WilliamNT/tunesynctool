from typing import Annotated
from fastapi import APIRouter, Depends, Request

from api.models.service import ProviderState, ProviderRead
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.security import oauth2_scheme
from api.helpers.service_driver import DRIVERS
from api.models.collection import Collection
from api.services.provider_service import ProviderService, get_provider_service

router = APIRouter(
    prefix="/providers",
    tags=["Providers"],
)

@router.get(
    path="/connected",
    summary="Get the list of all connected providers",
    operation_id="getConnectedProviders",
    name="providers:get_connected_providers",
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
    name="providers:get_valid_provider_names",
)
async def valid_providers(
    provider_service: Annotated[ProviderService, Depends(get_provider_service)],
    request: Request,
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> Collection[ProviderRead]:
    """
    Returns a list of all accepted provider names that clients can set in the `?provider=` query parameter across endpoints.

    An example use of this endpoint would be to populate a dropdown list in the client UI in a search field.
    """

    return provider_service.get_supported_providers(
        request=request
    )