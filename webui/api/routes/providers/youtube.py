from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse

from api.services.youtube_service import YouTubeService, get_youtube_service
from api.services.oauth2_linking.youtube_oauth2_handler import YouTubeOAuth2Handler, get_youtube_oauth2_handler
from api.core.security import oauth2_scheme

router = APIRouter(
    prefix="/providers/youtube",
    tags=["YouTube"],
)

@router.get(
    path="/authorize",
    status_code=302,
    responses={
        status.HTTP_302_FOUND: {
            "description": "Redirecting to YouTube authorization page.",
        },
    },
    summary="Start the YouTube Authorization Code Flow",
    operation_id="signInWithGoogle",
    name="youtube:authorize",
)
async def authorize(
    oauth2_handler: Annotated[YouTubeOAuth2Handler, Depends(get_youtube_oauth2_handler)],
    state: Annotated[str, Query()]
) -> RedirectResponse:
    """
    Starts the YouTube Authorization Code Flow. Redirects the user to the YouTube authorization page.
    The user will be asked to log in and authorize the application.

    Details: https://developers.google.com/identity/protocols/oauth2

    Takes a `state` parameter that includes metadata about the client.
    """
    
    return await oauth2_handler.request_user_authorization(
        state=state
    )

@router.get(
    path="/callback",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "The user granted access.",
        },
    },
    summary="Handle the YouTube Authorization Code Flow callback",
    include_in_schema=False,
    name="youtube:callback",
)
async def callback(
    oauth2_handler: Annotated[YouTubeOAuth2Handler, Depends(get_youtube_oauth2_handler)],
    state: str,
    code: Annotated[Optional[str], Query()] = None,
    error: Annotated[Optional[str], Query()] = None
) -> HTMLResponse:
    """
    Handles the Google OAuth2 callback.
    Do not call directly. This endpoint is called by Google after the user has authorized the application.

    Details: https://developers.google.com/youtube/v3/quickstart/python
    """
    
    return await oauth2_handler.handle_authorization_callback(
        state=state,
        code=code,
        error=error
    )

@router.delete(
    path="/unlink",
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Account unlinked successfully.",
        },
    },
    summary="Unlink YouTube",
    operation_id="unlinkYouTubeAccount",
    name="youtube:unlink_youtube_account",
)
async def unlink(
    provider_service: Annotated[YouTubeService, Depends(get_youtube_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Unlinks the Google account associated with the user.
    """

    return await provider_service.handle_account_unlink(jwt)