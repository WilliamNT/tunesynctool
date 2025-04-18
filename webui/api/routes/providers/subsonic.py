from typing import Annotated
from fastapi import APIRouter, Depends, status

from api.core.security import oauth2_scheme
from api.models.service import ProviderState
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.subsonic import SubsonicCredentials
from api.services.subsonic_service import SubsonicService, get_subsonic_service

router = APIRouter(
    prefix="/subsonic",
    tags=["subsonic"],
)

@router.post(
    path="/credentials",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Credentials set successfully.",
        },
    }
)
async def credentials(
    provider_service: Annotated[SubsonicService, Depends(get_subsonic_service)],
    credentials: SubsonicCredentials,
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Allows the user to set their Subsonic credentials.
    """

    return await provider_service.configure_credentials(
        credentials=credentials,
        jwt=jwt,
    )

@router.get(
    path="",
)
async def state(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> ProviderState:
    """
    Returns the status of the Subsonic provider.

    Call this endpoint to check if the user has connected their Subsonic account.
    """

    user = await auth_service.resolve_user_from_jwt(jwt)

    return await credentials_service.get_provider_state(
        user=user,
        service_name="subsonic",
    )

@router.delete(
    path="/unlink",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Account unlinked successfully.",
        },
    }
)
async def unlink(
    provider_service: Annotated[SubsonicService, Depends(get_subsonic_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Unlinks the Subsonic account associated with the user.
    """

    return await provider_service.handle_account_unlink(jwt)