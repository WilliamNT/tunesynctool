from fastapi import APIRouter, Depends
from typing import Annotated

from api.models.playlist import PlaylistRead
from api.models.collection import Collection
from api.core.security import oauth2_scheme
from api.services.library_service import LibraryService, get_library_service

router = APIRouter(
    prefix="/library",
    tags=["Library"],
)

@router.get(
    path="/playlists",
    summary="Get the user's playlists across all providers",
    operation_id="getLibraryPlaylists",
    name="library:get_playlists",
)
async def get_playlists(
    jwt: Annotated[str, Depends(oauth2_scheme)],
    library_service: Annotated[LibraryService, Depends(get_library_service)],
) -> Collection[PlaylistRead]:
    """
    Compiles a list of playlists the user owns and has saved to their library across all of their linked providers.

    Please note that this endpoint may not return up-to-date data because it relies on caching to prevent excessive API calls.

    Notes:
    - Some providers do not return all playlists (e.g. Spotify's automatically generated playlists).
    - Some providers do not support retrieving playlists that are saved but **not owned** by the linked account (e.g. YouTube).
    - This endpoint returns all playlists it finds. Checking wether 2 playlists are the same but synced is up to the client.
    """

    return await library_service.compile_user_playlists(
        jwt=jwt
    )