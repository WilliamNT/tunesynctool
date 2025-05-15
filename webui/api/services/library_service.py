from fastapi import Depends
from typing import Annotated, List
from tunesynctool.models.playlist import Playlist

from api.models.playlist import PlaylistRead
from api.models.collection import Collection
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.services.auth_service import AuthService, get_auth_service
from api.models.user import User
from api.services.catalog_service import CatalogService, get_catalog_service
from api.models.search import LookupLibraryPlaylistsParams
from api.services.service_driver_helper_service import ServiceDriverHelperService, get_service_driver_helper_service

class LibraryService:
    """
    A service to return content in the user's library.
    """

    def __init__(self, credentials_service: CredentialsService, auth_service: AuthService, catalog_service: CatalogService, service_driver_helper_service: Annotated[ServiceDriverHelperService, Depends(get_service_driver_helper_service)]) -> None:
        self.credentials_service = credentials_service
        self.auth_service = auth_service
        self.catalog_service = catalog_service
        self.service_driver_helper_service = service_driver_helper_service

    async def compile_user_playlists(self, jwt: str) -> Collection[PlaylistRead]:
        """
        Returns a list of playlists in the user's library across all linked providers.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)
        playlists = await self._get_playlists_for_user(user)

        return Collection(
            items=playlists,
        )
    
    async def _get_playlists_for_user(self, user: User) -> List[PlaylistRead]:

        services = await self.credentials_service.get_linked_providers(user)
        
        playlists = []
        for service in services:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                user=user,
                credentials=await self.credentials_service.get_service_credentials(
                    user=user,
                    service_name=service,
                ),
                provider_name=service,
            )

            provider_playlists = await self.catalog_service.compile_user_playlists(
                search_parameters=LookupLibraryPlaylistsParams(
                    provider=service,
                    limit=25 # TODO: add support for a negative or 0 value to get all playlists
                ),
                service_driver=driver
            )

            playlists.extend(provider_playlists.items)

        return playlists

def get_library_service(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    service_driver_helper_service: Annotated[ServiceDriverHelperService, Depends(get_service_driver_helper_service)],
) -> LibraryService:
    return LibraryService(
        credentials_service=credentials_service,
        auth_service=auth_service,
        catalog_service=catalog_service,
        service_driver_helper_service=service_driver_helper_service,
    )