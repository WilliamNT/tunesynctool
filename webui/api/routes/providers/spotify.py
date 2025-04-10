from typing import Annotated
from fastapi import APIRouter, Depends

from api.services.auth_service import AuthService, get_auth_service
from api.core.security import oauth2_scheme
from api.services.spotify_service import SpotifyService, get_spotify_service
from api.models.service import ProviderState
from api.services.credentials_service import CredentialsService, get_credentials_service

router = APIRouter(
    prefix="/spotify",
    tags=["spotify"],
)

@router.get("/authorize")
async def authorize(
    provider_service: Annotated[SpotifyService, Depends(get_spotify_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
):
    """
    Starts the Spotify Authorization Code Flow. Redirects the user to the Spotify authorization page.
    The user will be asked to log in and authorize the application.

    Details: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
    """

    return await provider_service.request_user_authorization(jwt)

@router.get("/callback")
async def callback(
    provider_service: Annotated[SpotifyService, Depends(get_spotify_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
    code: str,
):
    """
    Handles the Spotify Authorization Code Flow callback.
    Do not call directly. This endpoint is called by Spotify after the user has authorized the application.

    Details: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
    """

    return await provider_service.handle_authorization_callback(
        code=code,
        jwt=jwt,
    )

@router.get(
    path="/",
    response_model=ProviderState
)
async def state(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
):
    """
    Returns the status of the Spotify provider.

    Call this endpoint to check if the user has connected their Spotify account.
    """

    user = await auth_service.resolve_user_from_jwt(jwt)

    return await credentials_service.get_provider_state(
        user=user,
        service_name="spotify",
    )