from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse

from api.services.youtube_service import YouTubeService, get_youtube_service
from api.core.security import oauth2_scheme
from api.models.service import ProviderState
from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service

router = APIRouter(
    prefix="/youtube",
    tags=["youtube"],
)

@router.get(
    path="/authorize",
    status_code=302,
    responses={
        status.HTTP_302_FOUND: {
            "description": "Redirecting to YouTube authorization page.",
        },
    }
)
async def authorize(
    provider_service: Annotated[YouTubeService, Depends(get_youtube_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> RedirectResponse:
    """
    Starts the YouTube Authorization Code Flow. Redirects the user to the YouTube authorization page.
    The user will be asked to log in and authorize the application.

    Details: https://developers.google.com/identity/protocols/oauth2
    """
    
    return await provider_service.request_user_authorization(jwt)

@router.get(
    path="/callback",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "The user granted access.",
        },
    }
)
async def callback(
    provider_service: Annotated[YouTubeService, Depends(get_youtube_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
    request: Request
) -> None:
    """
    Handles the Google OAuth2 callback.
    Do not call directly. This endpoint is called by Google after the user has authorized the application.

    Details: https://developers.google.com/youtube/v3/quickstart/python
    """
    
    return await provider_service.handle_authorization_callback(
        callback_url=str(request.url),
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
    Returns the status of the YouTube provider.

    Call this endpoint to check if the user has connected their YouTube account.
    """

    user = await auth_service.resolve_user_from_jwt(jwt)

    return await credentials_service.get_provider_state(
        user=user,
        service_name="youtube",
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
    provider_service: Annotated[YouTubeService, Depends(get_youtube_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Unlinks the Google account associated with the user.
    """

    return await provider_service.handle_account_unlink(jwt)