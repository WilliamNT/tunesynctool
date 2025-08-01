from typing import Annotated

from fastapi import Depends
from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.exceptions import ServiceDriverException, UnsupportedFeatureException

from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.logging import logger
from api.models.search import LookupLibraryPlaylistsParams
from api.models.collection import Collection
from api.services.auth_service import AuthService, get_auth_service
from api.services.service_driver_helper_service import ServiceDriverHelperService, get_service_driver_helper_service
from api.models.playlist import PlaylistRead
from api.helpers.mapping import map_playlist_between_domain_model_to_response_model 
from api.models.user import User
from api.exceptions.http.provider import raise_unsupported_provider_exception
from api.exceptions.http.auth import raise_missing_or_invalid_auth_credentials_exception
from api.exceptions.http.service_driver import raise_service_driver_generic_exception, raise_unsupported_driver_feature_exception
from api.models.service import ServiceCredentials

class CatalogService:
    """
    Handles catalog operations.

    Provides an asynchronous abstraction for the tunesynctool package.
    """

    def __init__(
        self,
        credentials_service: CredentialsService,
        auth_service: AuthService,
        service_driver_helper_service: ServiceDriverHelperService,
    ) -> None:
        self.credentials_service = credentials_service
        self.auth_service = auth_service
        self.service_driver_helper_service = service_driver_helper_service
        

    async def handle_compilation_of_user_playlists(self, search_parameters: LookupLibraryPlaylistsParams, jwt: str) -> Collection[PlaylistRead]:
        user, credentials = await self.verify_user_and_credentials(jwt, search_parameters.provider, "look up their playlists at the provider")

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            raise_unsupported_provider_exception(
                provider_name=search_parameters.provider
            )

        return await self.compile_user_playlists(
            search_parameters=search_parameters,
            service_driver=driver
        )

    async def compile_user_playlists(self, search_parameters: LookupLibraryPlaylistsParams, service_driver: AsyncWrappedServiceDriver) -> Collection[PlaylistRead]:
        try:
            results = await service_driver.get_user_playlists(
                limit=search_parameters.limit
            )

            mapped_results = []
            for result in results:
                mapped_results.append(map_playlist_between_domain_model_to_response_model(
                    playlist=result,
                    provider_name=search_parameters.provider
                ))

            return Collection(
                items=mapped_results
            )
        except UnsupportedFeatureException as e:
            raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            raise_service_driver_generic_exception(
                provider_name=search_parameters.provider,
                e=e
            )

    async def verify_user_and_credentials(self, jwt, provider_name: str, fail_action_msg: str) -> tuple[User, ServiceCredentials]:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=provider_name,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{provider_name}\" but wanted to {fail_action_msg} anyway.")
            raise_missing_or_invalid_auth_credentials_exception(provider_name)

        return (user, credentials)

def get_catalog_service(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    service_driver_helper_service: Annotated[ServiceDriverHelperService, Depends(get_service_driver_helper_service)],
) -> CatalogService:
    return CatalogService(
        auth_service=auth_service,
        credentials_service=credentials_service,
        service_driver_helper_service=service_driver_helper_service,
    )