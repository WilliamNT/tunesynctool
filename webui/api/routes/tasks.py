from typing import Annotated
from fastapi import APIRouter, Depends, Query, Body, status

from api.models.track import TrackRead, TrackMatchCreate
from api.models.search import SearchParamsBase
from api.models.task import PlaylistTransferCreate, PlaylistTaskStatus
from api.core.security import oauth2_scheme
from api.services.track_matching_service import TrackMatchingService, get_track_matching_service
from api.core.context import RequestContext, get_request_context
from api.services.task_service import TaskService, get_task_service
from api.models.collection import Collection

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)

@router.post(
    path="/match",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Couldn't find a close enough match based on the provided metadata.",
        }
    },
    summary="Find the equivalent track on another provider",
    operation_id="matchTrack",
    name="tasks:match_track",
)
async def match_track(
    filter_query: Annotated[SearchParamsBase, Query()],
    body: Annotated[TrackMatchCreate, Body()],
    track_matching_service: Annotated[TrackMatchingService, Depends(get_track_matching_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> TrackRead:
    """
    Matches a track based on the provided metadata. Finding a match is not 100% guaranteed.

    **This can take anywhere from a few seconds to up to half a minute in extreme cases.**
    
    Notes:
    - The metadata provided is **not** used to populate the returned data.
    - The returned data is the closest match found by an automated search algorithm, not 100% guaranteed to be the same track.
    - The returned data may be a different version of the same track (e.g. live version, remix, etc.).
    - Do your own client-side validation to ensure the returned track is what you or your users expect.
    """
    
    return await track_matching_service.handle_matching(
        jwt=jwt,
        search_params=filter_query,
        reference_metadata=body
    )

@router.post(
    path="/transfer",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "The source playlist couldn't be found.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "The playlist is already being transferred."
        }
    },
    summary="Transfer a playlist to another provider",
    operation_id="transferPlaylist",
    name="tasks:transfer_playlist",
)
async def transfer_playlist(
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    body: Annotated[PlaylistTransferCreate, Body()],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> PlaylistTaskStatus:
    """
    Attempts to transfer the specified playlist from the source provider to the target provider.
    Replication is not guaranteed to be 100% successful.

    This starts a long running task. Clients can poll for the progress of the transfer.
    """

    return await service.dispatch_playlist_transfer(
        details=body,
        user=request_context.user
    )

@router.post(
    path="",
    summary="List all tasks",
    operation_id="getTasks",
    name="tasks:all_tasks",
)
async def all_tasks(
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> Collection[PlaylistTaskStatus]:
    """
    Returns all tasks belonging to the authenticated user, regardless of if they are running, in queue, or finished.
    The only exception is deleted tasks, for obvious reasons.
    """

    return await service.handle_compiling_tasks_for_user(
        user=request_context.user
    )