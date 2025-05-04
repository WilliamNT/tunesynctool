from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse

from api.services.auth_service import AuthService, get_auth_service
from api.core.security import oauth2_scheme
from api.services.spotify_service import SpotifyService, get_spotify_service
from api.services.credentials_service import CredentialsService, get_credentials_service

router = APIRouter(
    prefix="/providers/spotify",
    tags=["Spotify"],
)

@router.get(
    path="/authorize",
    status_code=302,
    responses={
        status.HTTP_302_FOUND: {
            "description": "Redirecting to Spotify authorization page.",
        },
    },
    summary="Start the Spotify Authorization Code Flow",
    operation_id="signInWithSpotify",
    name="spotify:authorize",
)
async def authorize(
    provider_service: Annotated[SpotifyService, Depends(get_spotify_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> RedirectResponse:
    """
    Starts the Spotify Authorization Code Flow. Redirects the user to the Spotify authorization page.
    The user will be asked to log in and authorize the application.

    Details: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
    """

    return await provider_service.request_user_authorization(jwt)
@router.get(
    path="/callback",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "The user granted access.",
        },
    },
    summary="Handle the Spotify Authorization Code Flow callback",
    include_in_schema=False,
    name="spotify:callback",
)
async def callback(
    provider_service: Annotated[SpotifyService, Depends(get_spotify_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
    code: str,
) -> HTMLResponse:
    """
    Handles the Spotify Authorization Code Flow callback.
    Do not call directly. This endpoint is called by Spotify after the user has authorized the application.

    Details: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
    """

    return await provider_service.handle_authorization_callback(
        code=code,
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
    summary="Unlink Spotify",
    operation_id="unlinkSpotifyAccount",
)
async def unlink(
    provider_service: Annotated[SpotifyService, Depends(get_spotify_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Unlinks the Spotify account associated with the user.
    """

    return await provider_service.handle_account_unlink(jwt)