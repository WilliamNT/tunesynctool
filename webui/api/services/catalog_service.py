from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.exceptions import ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException, PlaylistNotFoundException
from tunesynctool.models import Track, Playlist

from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.logging import logger
from api.models.search import SearchParams, ISRCSearchParams, LookupByProviderIDParams, LookupLibraryPlaylistsParams, SearchParamsBase
from api.models.collection import SearchResultCollection, Collection
from api.services.auth_service import AuthService, get_auth_service
from api.models.track import TrackRead
from api.models.entity import EntityMetaRead, EntitySingleAuthorRead, EntityIdentifiersBase, EntityAssetsBase
from api.services.service_driver_helper_service import ServiceDriverHelperService, get_service_driver_helper_service
from api.models.playlist import PlaylistRead, PlaylistCreate, PlaylistMultiTrackInsert
from api.helpers.mapping import map_track_between_domain_model_and_response_model, map_playlist_meta_from_domain_model_to_response_model
from api.helpers.extraction import extract_share_url_from_track_sync
from api.services.asset_service import AssetService, get_asset_service
from api.models.user import User
from api.exceptions.http.provider import raise_unsupported_provider_exception
from api.exceptions.http.auth import raise_missing_or_invalid_auth_credentials_exception
from api.exceptions.http.service_driver import raise_service_driver_generic_exception, raise_unsupported_driver_feature_exception

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
        asset_service: AssetService
    ) -> None:
        self.credentials_service = credentials_service
        self.auth_service = auth_service
        self.service_driver_helper_service = service_driver_helper_service
        self.asset_service = asset_service
        
    async def handle_search(self, search_parameters: SearchParams, jwt: str) -> SearchResultCollection[TrackRead]:
        """
        Handle search using the specified provider.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to search anyway.")
            raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

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

        results = await self.search(
            search_parameters=search_parameters,
            service_driver=driver,
            user=user
        )

        return SearchResultCollection(
            items=results,
            query=search_parameters.query
        )

    async def search(self, search_parameters: SearchParams, service_driver: AsyncWrappedServiceDriver, user: User) -> list[TrackRead]:
        try:
            results = await service_driver.search_tracks(
                query=search_parameters.query,
                limit=search_parameters.limit
            )

            if len(results) > search_parameters.limit:
                results = results[:search_parameters.limit]

            mapped_results = []
            for result in results:
                assets = await self.asset_service.get_track_assets(
                    search_parameters=LookupByProviderIDParams(
                        provider=search_parameters.provider,
                        provider_id=result.service_id
                    ),
                    user=user
                )

                mapped_results.append(map_track_between_domain_model_and_response_model(
                    track=result,
                    provider_name=search_parameters.provider,
                    assets=assets
                ))

            return mapped_results
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
    
    def _map_track_meta(self, track: Track, provider_name: str) -> EntityMetaRead:
        share_url = None
        extra_data = track.service_data
        
        sync_extractables = ["spotify", "youtube"]
        if track.service_name in sync_extractables:
            share_url = extract_share_url_from_track_sync(partial_data=extra_data, provider_name=provider_name)
        else:
            logger.debug(f"We either don't have an implementation for \"{provider_name}\" or it doesn't support it.")
        return EntityMetaRead(
            provider_name=provider_name,
            share_url=share_url
        ) 

    async def handle_isrc_search(self, search_parameters: ISRCSearchParams, jwt: str) -> TrackRead:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to look a track up by its ISRC anyway.")
            raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

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

        return await self.search_isrc(
            search_parameters=search_parameters,
            service_driver=driver,
            user=user
        )
    
    async def search_isrc(self, search_parameters: ISRCSearchParams, service_driver: AsyncWrappedServiceDriver, user: User) -> TrackRead:
        if not service_driver.supports_direct_isrc_querying:
            raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider
            )
            
        try:
            result = await service_driver.get_track_by_isrc(
                isrc=search_parameters.isrc
            )

            assets = await self.asset_service.get_track_assets(
                search_parameters=LookupByProviderIDParams(
                    provider=search_parameters.provider,
                    provider_id=result.service_id
                ),
                user=user
            )
            
            return map_track_between_domain_model_and_response_model(
                track=result,
                provider_name=search_parameters.provider,
                assets=assets
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
        except TrackNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail=f"Track not found.",
            ) from e

    async def handle_track_lookup(self, search_parameters: LookupByProviderIDParams, jwt: str) -> TrackRead:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to look a track up by its ID anyway.")
            raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

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

        return await self.track_lookup(
            search_parameters=search_parameters,
            service_driver=driver,
            user=user
        )
    
    async def track_lookup(self, search_parameters: LookupByProviderIDParams, service_driver: AsyncWrappedServiceDriver, user: User) -> TrackRead:
        try:
            result = await service_driver.get_track(
                track_id=search_parameters.provider_id
            )

            assets = await self.asset_service.get_track_assets(
                search_parameters=LookupByProviderIDParams(
                    provider=search_parameters.provider,
                    provider_id=result.service_id
                ),
                user=user
            )

            return map_track_between_domain_model_and_response_model(
                track=result,
                provider_name=search_parameters.provider,
                assets=assets
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
        except TrackNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail=f"Track not found.",
            ) from e

    async def handle_playlist_lookup(self, search_parameters: LookupByProviderIDParams, jwt: str) -> PlaylistRead:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to look a playlist up by its ID anyway.")
            raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

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

        return await self.playlist_lookup(
            search_parameters=search_parameters,
            service_driver=driver
        )

    async def playlist_lookup(self, search_parameters: LookupByProviderIDParams, service_driver: AsyncWrappedServiceDriver) -> PlaylistRead:
        try:
            result = await service_driver.get_playlist(
                playlist_id=search_parameters.provider_id
            )

            return self._map_playlist(
                playlist=result,
                provider_name=search_parameters.provider
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
        except PlaylistNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail=f"Playlist not found.",
            ) from e
        
    def _map_playlist(self, playlist: Playlist, provider_name: str) -> PlaylistRead:
        meta = map_playlist_meta_from_domain_model_to_response_model(
            playlist=playlist,
            provider_name=provider_name
        )

        author = EntitySingleAuthorRead(
            primary=playlist.author_name
        )

        identifiers = EntityIdentifiersBase(
            provider_id=str(playlist.service_id)
        )

        assets = self._map_playlist_assets(
            playlist=playlist
        )

        return PlaylistRead(
            title=playlist.name,
            description=playlist.description,
            is_public=playlist.is_public,
            author=author,
            meta=meta,
            identifiers=identifiers,
            assets=assets
        )
    
    def _map_playlist_assets(self, playlist: Playlist) -> EntityAssetsBase:
        link = None
        extra_data = playlist.service_data

        match playlist.service_name:
            case "spotify":
                link = extra_data.get("images", [])[0].get("url") if extra_data.get("images") and len(extra_data.get("images")) > 0 else None
            case "youtube":
                link = extra_data.get("thumbnails", {})[0].get("url") if extra_data.get("thumbnails") and len(extra_data.get("thumbnails")) > 0 else None
            case "deezer", "subsonic":
                # TODO: add support for Deezer and Subsonic playlist cover art
                pass

        return EntityAssetsBase(
            cover_image=link
        )
    
    async def handle_playlist_tracks_lookup(self, search_parameters: LookupByProviderIDParams, jwt: str) -> Collection[TrackRead]:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to look a playlist's tracks up by its ID anyway.")
            raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

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

        return await self.playlist_tracks_lookup(
            search_parameters=search_parameters,
            service_driver=driver,
            user=user
        )

    async def playlist_tracks_lookup(self, search_parameters: LookupByProviderIDParams, service_driver: AsyncWrappedServiceDriver, user: User) -> Collection[TrackRead]:
        try:
            results = await service_driver.get_playlist_tracks(
                playlist_id=search_parameters.provider_id,
                limit=0
            )

            mapped_results = []
            for result in results:
                assets = await self.asset_service.get_track_assets(
                    search_parameters=LookupByProviderIDParams(
                        provider=search_parameters.provider,
                        provider_id=result.service_id
                    ),
                    user=user
                )
                    
                mapped_results.append(map_track_between_domain_model_and_response_model(
                    track=result,
                    provider_name=search_parameters.provider,
                    assets=assets
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
        except PlaylistNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail=f"Playlist not found.",
            ) from e
        
    async def handle_compilation_of_user_playlists(self, search_parameters: LookupLibraryPlaylistsParams, jwt: str) -> Collection[PlaylistRead]:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to look up their playlists at the provider anyway.")
            raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

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
                mapped_results.append(self._map_playlist(
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

    async def handle_playlist_creation(self, search_parameters: SearchParamsBase, playlist_details: PlaylistCreate, jwt: str) -> PlaylistRead:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to create a playlist anyway.")
            raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

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

        return await self.create_playlist(
            search_parameters=search_parameters,
            playlist_details=playlist_details,
            service_driver=driver
        )
    
    async def create_playlist(self, search_parameters: SearchParamsBase, playlist_details: PlaylistCreate, service_driver: AsyncWrappedServiceDriver) -> PlaylistRead:
        try:
            result = await service_driver.create_playlist(
                name=playlist_details.title,
            )

            return self._map_playlist(
                playlist=result,
                provider_name=search_parameters.provider
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

    async def handle_adding_track_to_playlist(self, search_parameters: LookupByProviderIDParams, track_details: PlaylistMultiTrackInsert, jwt: str) -> Collection[TrackRead]:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to add one or more tracks to a playlist anyway.")
            raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

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

        return await self.add_track_to_playlist(
            search_parameters=search_parameters,
            track_details=track_details,
            service_driver=driver
        )
    
    async def add_track_to_playlist(self, search_parameters: LookupByProviderIDParams, track_details: PlaylistMultiTrackInsert, service_driver: AsyncWrappedServiceDriver) -> Collection[TrackRead]:
        try:
            await service_driver.add_tracks_to_playlist(
                playlist_id=search_parameters.provider_id,
                track_ids=track_details.provider_ids
            )

            return await self.playlist_tracks_lookup(
                search_parameters=search_parameters,
                service_driver=service_driver
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
        except PlaylistNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail=f"Playlist not found.",
            ) from e
        except TrackNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail=f"Track not found.",
            ) from e

def get_catalog_service(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    service_driver_helper_service: Annotated[ServiceDriverHelperService, Depends(get_service_driver_helper_service)],
    asset_service: Annotated[AssetService, Depends(get_asset_service)]
) -> CatalogService:
    return CatalogService(
        auth_service=auth_service,
        credentials_service=credentials_service,
        service_driver_helper_service=service_driver_helper_service,
        asset_service=asset_service
    )