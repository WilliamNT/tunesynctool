from typing import Annotated
from fastapi import APIRouter, Depends, status

from api.core.security import oauth2_scheme
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.deezer_arl import ARLCreate
from api.services.deezer_service import DeezerService, get_deezer_service

router = APIRouter(
    prefix="/providers/deezer",
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
    name="deezer:set_deezer_arl",
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
    name="deezer:unlink_deezer_account",
)
async def unlink(
    provider_service: Annotated[DeezerService, Depends(get_deezer_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Unlinks the Deezer account associated with the user.
    """

    return await provider_service.handle_account_unlink(jwt)