from typing import Annotated
from fastapi import APIRouter, Depends

from api.models.service import ProviderState
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.security import oauth2_scheme

from .spotify import router as spotify_router
from .deezer import router as deezer_router
from .subsonic import router as subsonic_router
from .youtube import router as youtube_router

router = APIRouter(
    prefix="/providers",
)

router.include_router(spotify_router)
router.include_router(deezer_router)
router.include_router(subsonic_router)
router.include_router(youtube_router)

@router.get(
    path="/connected",
    tags=["providers"],
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