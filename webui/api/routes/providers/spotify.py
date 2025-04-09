from typing import Annotated
from fastapi import APIRouter, Depends

from api.services.auth_service import AuthService, get_auth_service
from api.core.security import oauth2_scheme
from api.services.spotify_service import SpotifyService, get_spotify_service

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
    Starts the Spotify Authorization Code Flow.

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

    Details: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
    """

    return await provider_service.handle_authorization_callback(
        code=code,
        jwt=jwt,
    )

@router.get("")
async def test(
    provider_service: Annotated[SpotifyService, Depends(get_spotify_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
):
    """
    Test endpoint for the Spotify provider.
    """

    data =  await provider_service.credentials_service.get_service_credentials(
        user=await provider_service.auth_service.resolve_user_from_jwt(jwt),
        service_name="spotify",
    )

    return data.credentials