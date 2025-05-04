from typing import Annotated
from fastapi import APIRouter, Depends, status

from api.core.security import oauth2_scheme
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.subsonic import SubsonicCredentials
from api.services.subsonic_service import SubsonicService, get_subsonic_service

router = APIRouter(
    prefix="/providers/subsonic",
    tags=["Subsonic"],
)

@router.post(
    path="/credentials",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Credentials set successfully.",
        },
    },
    summary="Set the Subsonic credentials",
    operation_id="setSubsonicCredentials",
    name="subsonic:set_subsonic_credentials",
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

@router.delete(
    path="/unlink",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Account unlinked successfully.",
        },
    },
    summary="Unlink Subsonic",
    operation_id="unlinkSubsonicAccount",
    name="subsonic:unlink_subsonic_account",
)
async def unlink(
    provider_service: Annotated[SubsonicService, Depends(get_subsonic_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Unlinks the Subsonic account associated with the user.
    """

    return await provider_service.handle_account_unlink(jwt)