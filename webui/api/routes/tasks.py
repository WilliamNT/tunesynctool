from typing import Annotated
from fastapi import APIRouter, Depends, Query, Body, status

from api.models.track import TrackRead, TrackMatchCreate
from api.models.search import SearchParamsBase
from api.core.security import oauth2_scheme
from api.services.track_matching_service import TrackMatchingService, get_track_matching_service

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
    operation_id="matchTrack"
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