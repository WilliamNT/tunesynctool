from typing import Annotated
from fastapi import APIRouter, Body, Depends, Request

from api.models.service import ProviderRead
from api.services.auth_service import AuthService, get_auth_service
from api.core.security import oauth2_scheme
from api.models.collection import Collection
from api.services.provider_service import ProviderService, get_provider_service
from api.models.token import AccessToken
from api.models.state import OAuth2StateCreate

router = APIRouter(
    prefix="/providers",
    tags=["Providers"],
)

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

    return await provider_service.get_supported_providers(
        request=request,
        jwt=jwt
    )

@router.post(
    path="/{provider_name}/state",
    summary="Generate a state for the provider",
    operation_id="generateProviderState",
    name="providers:generate_provider_state",
    responses={
        200: {
            "description": "The state was generated successfully.",
        },
    },
)
async def generate_provider_state(
    provider_name: str,
    details: Annotated[OAuth2StateCreate, Body()],
    jwt: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> AccessToken:
    """
    Generates a signed state to be used for OAuth2 authentication flows.

    This is required for providers that users can link by going through an OAuth2 flow.
    """

    return await auth_service.generate_oauth2_state(
        provider_name=provider_name,
        jwt=jwt,
        details=details
    )