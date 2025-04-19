from typing import Annotated
from fastapi import APIRouter, Depends

from api.models.service import ProviderState
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.security import oauth2_scheme

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
) -> list[ProviderState]:
    """
    Get the list of all **connected** providers.
    """
    
    user = await auth_service.resolve_user_from_jwt(jwt)
    return await credentials_service.get_states_of_all_connected_providers(user)