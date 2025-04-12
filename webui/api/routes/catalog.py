from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from api.services.catalog_service import CatalogService, get_catalog_service
from api.models.search import SearchParams
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
) -> list[TrackRead]:
    """
    Search using the specified provider. This is basically a proxy.

    Results are returned in the order they are received from the provider, meaning you should not rely on their order.

    Note: Content other than **tracks** (e.g. podcasts, albums, etc.) are omitted from the results.
    """

    return await catalog_service.handle_search(
        search_parameters=filter_query,
        jwt=jwt
    )