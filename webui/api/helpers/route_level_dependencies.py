from fastapi import Path, Query
from typing import Annotated

from api.models.search import LookupByProviderIDParams, ISRCSearchParams, LookupLibraryPlaylistsParams

PROVIDER_ALIAS = Annotated[str, Query()]

def get_lookup_by_provider_id_params(
    provider: PROVIDER_ALIAS,
    provider_id: Annotated[str, Path()]
) -> LookupByProviderIDParams:
    return LookupByProviderIDParams(
        provider=provider,
        provider_id=provider_id
    )

def get_isrc_search_params(
    provider: PROVIDER_ALIAS,
    isrc: Annotated[str, Path()],
) -> ISRCSearchParams:
    return ISRCSearchParams(
        provider=provider,
        isrc=isrc
    )

def get_lookup_library_playlists_params(
    provider: PROVIDER_ALIAS,
    limit: Annotated[int, Query()]
) -> LookupLibraryPlaylistsParams:
    return LookupLibraryPlaylistsParams(
        provider=provider,
        limit=limit
    )