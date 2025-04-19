from typing import Annotated
from fastapi import APIRouter, Depends, status

from api.core.security import oauth2_scheme
from api.models.service import ProviderState
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.deezer_arl import ARLCreate
from api.services.deezer_service import DeezerService, get_deezer_service

router = APIRouter(
    prefix="/deezer",
    tags=["Deezer"],
)

@router.post(
    path="/arl",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "ARL set successfully.",
        },
    },
    summary="Set the Deezer ARL cookie",
    operation_id="setDeezerARL",
)
async def arl(
    provider_service: Annotated[DeezerService, Depends(get_deezer_service)],
    arl: ARLCreate,
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Allows the user to set their Deezer ARL cookie.
    """

    return await provider_service.configure_arl(
        arl=arl,
        jwt=jwt,
    )

@router.get(
    path="",
    summary="Get the Deezer provider state",
    operation_id="getDeezerProviderState",
)
async def state(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> ProviderState:
    """
    Returns the status of the Deezer provider.

    Call this endpoint to check if the user has connected their Deezer account.
    """

    user = await auth_service.resolve_user_from_jwt(jwt)

    return await credentials_service.get_provider_state(
        user=user,
        service_name="deezer",
    )

@router.delete(
    path="/unlink",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Account unlinked successfully.",
        },
    },
    summary="Unlink Deezer",
    operation_id="unlinkDeezerAccount",
)
async def unlink(
    provider_service: Annotated[DeezerService, Depends(get_deezer_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Unlinks the Deezer account associated with the user.
    """

    return await provider_service.handle_account_unlink(jwt)