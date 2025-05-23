from typing import Annotated
from fastapi import APIRouter, Depends, Query, status, Body

from api.services.catalog_service import CatalogService, get_catalog_service
from api.models.search import SearchParams, ISRCSearchParams, LookupByProviderIDParams, LookupLibraryPlaylistsParams, SearchParamsBase
from api.models.collection import SearchResultCollection, Collection
from api.models.track import TrackRead
from api.core.security import oauth2_scheme
from api.models.playlist import PlaylistCreate, PlaylistRead, PlaylistMultiTrackInsert
from api.helpers.route_level_dependencies import get_lookup_by_provider_id_params, get_isrc_search_params

router = APIRouter(
    tags=["Catalog"],
)

@router.get(
    path="/search",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details.",
        }
    },
    summary="Search for tracks",
    operation_id="searchTracks",
    name="catalog:search_tracks",
)
async def search(
    filter_query: Annotated[SearchParams, Query()],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> SearchResultCollection[TrackRead]:
    """
    Search using the specified provider. This is basically a proxy.

    Results are returned in the order they are received from the provider, meaning you should not rely on their order.

    Notes:
    - Content other than **tracks** (e.g. podcasts, albums, etc.) are omitted from the results if this type of filtering is supported by the provider.
    - For YouTube, results are limited to **any video** that belongs to the "**Music**" category. This means that the results may include irrelevant content.
    - YouTube results may include results from "Topic" channels, which are not actual artist channels.
    """

    return await catalog_service.handle_search(
        search_parameters=filter_query,
        jwt=jwt
    )

@router.get(
    path="/isrc/{isrc}",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The provider didn't return a match for the given ISRC.",
        }
    },
    summary="Get a track by its ISRC",
    operation_id="getTrackByISRC",
    name="catalog:get_track_by_isrc",
)
async def search_isrc(
    filter_query: Annotated[ISRCSearchParams, Depends(get_isrc_search_params)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> TrackRead:
    """
    Search using the specified provider by a specific ISRC identifier. This is basically a proxy.
    
    Notes:
    - Not all providers support direct ISRC search. If this is the case, an error will be returned.
    """

    return await catalog_service.handle_isrc_search(
        search_parameters=filter_query,
        jwt=jwt
    )

@router.get(
    path="/tracks/{provider_id}",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The provider didn't return a match for the given track ID.",
        }
    },
    summary="Get a track by its ID",
    operation_id="getTrack",
    name="catalog:get_track_by_id",
)
async def get_track(
    filter_query: Annotated[LookupByProviderIDParams, Depends(get_lookup_by_provider_id_params)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> TrackRead:
    """
    Retrieve a track by its ID from the specified provider. This is basically a proxy.
    
    Notes:
    - Some providers (like Spotify) may support multiple ID formats. In these cases, all formats are supported.
    """

    return await catalog_service.handle_track_lookup(
        search_parameters=filter_query,
        jwt=jwt
    )

@router.get(
    path="/playlists/{provider_id}",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The provider didn't return a match for the given playlist ID.",
        }
    },
    summary="Get a playlist by its ID",
    operation_id="getPlaylist",
    name="catalog:get_playlist_by_id",
)
async def get_playlist(
    filter_query: Annotated[LookupByProviderIDParams, Depends(get_lookup_by_provider_id_params)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> PlaylistRead:
    """
    Retrieve a playlist by its ID from the specified provider. This is basically a proxy.
    
    Notes:
    - Some providers (like Spotify) may support multiple ID formats. In these cases, all formats are supported.
    """

    return await catalog_service.handle_playlist_lookup(
        search_parameters=filter_query,
        jwt=jwt
    )

@router.get(
    path="/playlists/{provider_id}/tracks",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The provider didn't return a match for the given playlist ID.",
        }
    },
    summary="Get all tracks from a playlist",
    operation_id="getPlaylistTracks",
    name="catalog:get_playlist_tracks_by_id",
)
async def get_playlist_tracks(
    filter_query: Annotated[LookupByProviderIDParams, Depends(get_lookup_by_provider_id_params)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> Collection[TrackRead]:
    """
    Retrieve a playlist by its ID from the specified provider. This is basically a proxy.
    
    Notes:
    - Some providers (like Spotify) may support multiple ID formats. In these cases, all formats are supported.
    """

    return await catalog_service.handle_playlist_tracks_lookup(
        search_parameters=filter_query,
        jwt=jwt
    )

@router.get(
    path="/playlists",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details."
        }
    },
    summary="Get playlists owned (and saved) by the user",
    operation_id="getSavedPlaylists",
    name="catalog:get_saved_playlists",
)
async def get_saved_playlists(
    filter_query: Annotated[LookupLibraryPlaylistsParams, Query()],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> Collection[PlaylistRead]:
    """
    Returns all playlists the user owns or has saved to their library on the specified provider.
    Keep in mind that results may not be exhaustive.
    Some providers may not return all playlists like those that are automatically generated.

    Notes:
    - YouTube does not support retrieving playlists that are saved but **not owned** by the linked account.
    - YouTube results are not filtered to only contain music related playlists (e.g. any owned playlist will be returned).
    """

    return await catalog_service.handle_compilation_of_user_playlists(
        search_parameters=filter_query,
        jwt=jwt
    )

@router.post(
    path="/playlists",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details."
        },
        status.HTTP_200_OK: {
            "description": "Playlist created successfully."
        }
    },
    summary="Create a new playlist",
    operation_id="createPlaylist",
    name="catalog:create_playlist",
)
async def create_playlist(
    filter_query: Annotated[SearchParamsBase, Query()],
    playlist_details: Annotated[PlaylistCreate, Body()],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> PlaylistRead:
    """
    Create a new playlist on the specified provider.

    To keep things uniform, you cannot add initial tracks to the playlist because not all providers support this.
    """

    return await catalog_service.handle_playlist_creation(
        playlist_details=playlist_details,
        search_parameters=filter_query,
        jwt=jwt
    )

@router.post(
    path="/playlists/{provider_id}/tracks",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details."
        },
        status.HTTP_200_OK: {
            "description": "Track added successfully."
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The provider didn't return a match for the given playlist ID or one or more of the supplied track IDs are invalid.",
        }
    },
    summary="Add tracks to a playlist",
    operation_id="addTrackToPlaylist",
    name="catalog:add_track_to_playlist",
)
async def add_tracks_to_playlist(
    filter_query: Annotated[LookupByProviderIDParams, Depends(get_lookup_by_provider_id_params)],
    track_details: Annotated[PlaylistMultiTrackInsert, Body()],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    jwt: Annotated[str, Depends(oauth2_scheme)]
) -> Collection[TrackRead]:
    """
    Add a track to a playlist on the specified provider.
    """

    return await catalog_service.handle_adding_track_to_playlist(
        track_details=track_details,
        search_parameters=filter_query,
        jwt=jwt
    )