from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse, Response

from api.services.oauth2_linking.spotify_oauth2_handler import SpotifyOAuth2Handler, get_spotify_oauth2_handler
from api.core.context import RequestContext, get_request_context
from api.services.providers.base_provider import BaseProvider
from api.services.providers.provider_factory import get_provider_in_route

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
    oauth2_handler: Annotated[SpotifyOAuth2Handler, Depends(get_spotify_oauth2_handler)],
    state: Annotated[str, Query()]
) -> RedirectResponse:
    """
    Starts the Spotify Authorization Code Flow. Redirects the user to the Spotify authorization page.
    The user will be asked to log in and authorize the application.

    Details: https://developer.spotify.com/documentation/web-api/tutorials/code-flow

    Takes a `state` parameter that includes metadata about the client.
    """

    return await oauth2_handler.request_user_authorization(
        state=state
    )

@router.get(
    path="/callback",
    status_code=200,
    responses={
        status.HTTP_200_OK: {
            "description": "The user granted access. A default HTML page is shown.",
        },
        status.HTTP_302_FOUND: {
            "description": "Redirecting to the specified redirect_uri.",
        },
    },
    summary="Handle the Spotify Authorization Code Flow callback",
    include_in_schema=False,
    name="spotify:callback",
)
async def callback(
    oauth2_handler: Annotated[SpotifyOAuth2Handler, Depends(get_spotify_oauth2_handler)],
    state: str,
    code: Annotated[Optional[str], Query()] = None,
    error: Annotated[Optional[str], Query()] = None
) -> Response:
    """
    Handles the Spotify Authorization Code Flow callback.
    Do not call directly. This endpoint is called by Spotify after the user has authorized the application.

    If the client specified a `redirect_uri` in the original request, the user will be redirected to that URI after authorization.
    Otherwise, the user will see a basic success page.

    Details: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
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
    summary="Unlink Spotify",
    operation_id="unlinkSpotifyAccount",
)
async def unlink(
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    provider: Annotated[BaseProvider, Depends(get_provider_in_route)]
) -> None:
    """
    Unlinks the Spotify account associated with the user.
    """

    return await provider.handle_account_unlink(
        user=request_context.user
    )