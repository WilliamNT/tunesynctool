from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from api.services.catalog_service import CatalogService, get_catalog_service
from api.models.search import SearchParams, ISRCSearchParams, LookupByProviderIDParams
from api.models.collection import SearchResultCollection
from api.models.track import TrackRead
from api.core.security import oauth2_scheme

router = APIRouter(
    tags=["catalog"],
)

@router.get(
    path="/search",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Something went wrong with the provider. See message for details.",
        }
    }
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
    }
)
async def search_isrc(
    filter_query: Annotated[ISRCSearchParams, Query()],
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
    }
)
async def get_track(
    filter_query: Annotated[LookupByProviderIDParams, Query()],
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