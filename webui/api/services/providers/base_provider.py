from typing import Awaitable, Callable, Optional, TypeVar
from fastapi import HTTPException, status
from tunesynctool.drivers.async_service_driver import AsyncWrappedServiceDriver
from tunesynctool.exceptions import PlaylistNotFoundException, ServiceDriverException, TrackNotFoundException, UnsupportedFeatureException
from tunesynctool.models.track import Track
import asyncio

from api.services.credentials_service import CredentialsService
from api.models.service import ServiceCredentials, ServiceCredentialsCreate
from api.models.user import User
from api.models.search import ISRCSearchParams, LookupByProviderIDParams, LookupLibraryPlaylistsParams, SearchParams, SearchParamsBase
from api.models.collection import Collection, SearchResultCollection
from api.models.track import TrackRead
from api.services.factories.service_driver_factory import ServiceDriverFactory
from api.exceptions.http.provider import raise_unsupported_provider_exception
from api.exceptions.http.service_driver import raise_service_driver_generic_exception, raise_unsupported_driver_feature_exception
from api.helpers.mapping import map_track_between_domain_model_and_response_model, map_playlist_between_domain_model_to_response_model
from api.models.entity import EntityAssetsBase
from api.helpers.extraction import extract_cover_link_for_track_sync
from api.models.playlist import PlaylistCreate, PlaylistMultiTrackInsert, PlaylistRead

class BaseProvider:
    def __init__(self, credentials_service: CredentialsService, provider_name: str):
        self.credentials_service = credentials_service
        self.provider_name = provider_name

        self.service_driver_factory = ServiceDriverFactory(
            provider_name=provider_name,
            credentials_service=credentials_service
        )

    async def _get_driver(self, user: User) -> AsyncWrappedServiceDriver:
        try:
            return await self.service_driver_factory.create(user)
        except ValueError:
            raise_unsupported_provider_exception(self.provider_name)

    async def get_credentials(self, user: User) -> Optional[ServiceCredentials]:
        """
        Retrieves credentials for the given provider and user.
        """

        return await self.credentials_service.get_service_credentials(
            user=user,
            service_name=self.provider_name
        )

    async def set_credentials(self, credentials: ServiceCredentialsCreate, user: User) -> ServiceCredentials:
        """
        Saves new credentials, **or overwrites them if they already exist** for the specified user and provider.
        """

        if credentials.service_name != self.provider_name:
            raise ValueError(f"Provider \"{self.provider_name}\" can only set credentials for its own kind, not \"{credentials.service_name}\". Did you pass the wrong variable?")

        return await self.credentials_service.set_service_credentials(
            user=user,
            credentials=credentials
        )
    
    async def _delete_credentials(self, user: User, log_reason: Optional[str] = None) -> None:
        """
        Deletes the credentials for the given user and provider.
        Can be safely called even if the credentials don't exist.

        Note: This is meant for internal use. To properly unlink a provider's credentials, user the `handle_account_unlink()` method instead.
        """
        
        await self.credentials_service.delete_credentials(
            user=user,
            service_name=self.provider_name,
            log_reason=log_reason
        )

    async def handle_track_search(self, search_parameters: SearchParams, user: User) -> SearchResultCollection[TrackRead]:
        """
        Search the provider's catalog for tracks.
        """

        driver = await self._get_driver(user)
        results = await self._exec_service_driver_method(lambda: driver.search_tracks(query=search_parameters.query, limit=search_parameters.limit))

        if len(results) > search_parameters.limit:
            results = results[:search_parameters.limit]

        assets_list = await asyncio.gather(*[self.get_track_assets(result, user) for result in results])
        mapped_results = [
            map_track_between_domain_model_and_response_model(
                track=result,
                provider_name=self.provider_name,
                assets=assets
            ) for result, assets in zip(results, assets_list)
        ]

        return SearchResultCollection(
            items=mapped_results,
            query=search_parameters.query
        )

    async def get_track_assets(self, track: Track, user: User) -> EntityAssetsBase:
        """
        Retrieves (or extracts) the track assets from the track object.

        Is async because some providers require us to send extra requests.
        """
        
        url = extract_cover_link_for_track_sync(
            partial_data=track.service_data,
            provider_name=self.provider_name
        )

        return EntityAssetsBase(
            cover_image=url
        )

    async def handle_isrc_search(self, search_parameters: ISRCSearchParams, user: User) -> TrackRead:
        """
        Attempts to resolve the track that is identified by the given ISRC.
        """

        driver = await self._get_driver(user)
        if not driver.supports_direct_isrc_querying:
            raise_unsupported_driver_feature_exception(
                provider_name=self.provider_name
            )

        try:
            result = await self._exec_service_driver_method(lambda: driver.get_track_by_isrc(isrc=search_parameters.isrc))
            assets = await self.get_track_assets(result, user)

            return map_track_between_domain_model_and_response_model(
                track=result,
                provider_name=self.provider_name,
                assets=assets
            )
        except TrackNotFoundException as e:
            raise HTTPException(
                detail="Track not found.",
                status_code=status.HTTP_404_NOT_FOUND
            ) from e

    async def handle_track_lookup(self, search_paremeters: LookupByProviderIDParams, user: User) -> TrackRead:
        """
        Attempts to resolve the track that is identified by the given provider ID.
        """

        try:
            driver = await self._get_driver(user)
            result = await self._exec_service_driver_method(lambda: driver.get_track(track_id=search_paremeters.provider_id))
            assets = await self.get_track_assets(result, user)

            return map_track_between_domain_model_and_response_model(
                track=result,
                provider_name=self.provider_name,
                assets=assets
            )
        except TrackNotFoundException as e:
            raise HTTPException(
                detail="Track not found.",
                status_code=status.HTTP_404_NOT_FOUND
            ) from e

    async def handle_playlist_lookup(self, search_parameters: LookupByProviderIDParams, user: User) -> PlaylistRead:
        """
        Attempts to resolve the playlist that is identified by the given provider ID.
        """
        
        try:
            driver = await self._get_driver(user)
            result = await self._exec_service_driver_method(lambda: driver.get_playlist(playlist_id=search_parameters.provider_id))

            return map_playlist_between_domain_model_to_response_model(
                playlist=result,
                provider_name=self.provider_name
            )
        except PlaylistNotFoundException as e:
            raise HTTPException(
                detail="Playlist not found.",
                status_code=status.HTTP_404_NOT_FOUND
            ) from e

    async def handle_playlist_tracks_lookup(self, search_parameters: LookupByProviderIDParams, user: User) -> Collection[TrackRead]:
        """
        Retrieves tracks for a given playlist.
        """

        try:
            driver = await self._get_driver(user)
            results = await self._exec_service_driver_method(lambda: driver.get_playlist_tracks(playlist_id=search_parameters.provider_id, limit=0))

            assets_list = await asyncio.gather(*[self.get_track_assets(result, user) for result in results])
            mapped_results = [
                map_track_between_domain_model_and_response_model(
                    track=result,
                    provider_name=self.provider_name,
                    assets=assets
                ) for result, assets in zip(results, assets_list)
            ]

            return Collection(
                items=mapped_results
            )
        except PlaylistNotFoundException as e:
            raise HTTPException(
                detail="Playlist not found.",
                status_code=status.HTTP_404_NOT_FOUND
            ) from e

    async def handle_user_playlists_listing(self, search_parameters: LookupLibraryPlaylistsParams, user: User) -> Collection[PlaylistRead]:
        """
        Retrieves all user playlists up to the limit.
        """
        
        driver = await self._get_driver(user)
        results = await self._exec_service_driver_method(lambda: driver.get_user_playlists(limit=search_parameters.limit))

        if len(results) > search_parameters.limit:
            results = results[:search_parameters.limit]

        mapped_results = [
            map_playlist_between_domain_model_to_response_model(
                playlist=result,
                provider_name=self.provider_name
            ) for result in results
        ]

        return Collection(
            items=mapped_results
        )
    
    async def handle_playlist_creation(self, search_parameters: SearchParamsBase, playlist_details: PlaylistCreate, user: User) -> PlaylistRead:
        """
        Creates a new playlist at the specified provider with the given paremeters.
        """

        driver = await self._get_driver(user)
        result = await self._exec_service_driver_method(lambda: driver.create_playlist(name=playlist_details.title))

        return map_playlist_between_domain_model_to_response_model(
            playlist=result,
            provider_name=self.provider_name
        )
    
    async def handle_adding_tracks_to_a_playlist(self, search_parameters: LookupByProviderIDParams, track_details: PlaylistMultiTrackInsert, user: User) -> Collection[TrackRead]:
        """
        Adds the tracks associated with the supplied track IDs to the specified playlist.
        """

        try:
            driver = await self._get_driver(user)
            await self._exec_service_driver_method(lambda: driver.add_tracks_to_playlist(playlist_id=search_parameters.provider_id, track_ids=track_details.provider_ids))

            return await self.handle_playlist_tracks_lookup(
                search_parameters=search_parameters,
                user=user
            )
        except PlaylistNotFoundException as e:
            raise HTTPException(
                detail="Playlist not found.",
                status_code=status.HTTP_404_NOT_FOUND
            ) from e
        except TrackNotFoundException as e:
            raise HTTPException(
                detail="At least one track was not found at the provider.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    T = TypeVar("T")
    async def _exec_service_driver_method(self, async_lambda: Callable[[], Awaitable[T]]) -> T:
        try:
            return await async_lambda()
        except UnsupportedFeatureException as e:
            raise_unsupported_driver_feature_exception(
                provider_name=self.provider_name,
                e=e
            )
        except ServiceDriverException as e:
            raise_service_driver_generic_exception(
                provider_name=self.provider_name,
                e=e
            )

    async def handle_account_unlink(self, user: User) -> None:
        await self._delete_credentials(
            user=user,
            log_reason="Integration unlinked by user."
        )

    async def handle_saved_tracks_lookup(self, search_parameters: LookupLibraryPlaylistsParams, user: User) -> Collection[TrackRead]:
        """
        Lists the tracks in the user's "liked music" playlist, if the provider supports it.
        """

        driver = await self._get_driver(user)
        results = await self._exec_service_driver_method(lambda: driver.get_saved_tracks(limit=search_parameters.limit))

        if len(results) > search_parameters.limit:
            results = results[:search_parameters.limit]

        assets_list = await asyncio.gather(*[self.get_track_assets(result, user) for result in results])
        mapped_results = [
            map_track_between_domain_model_and_response_model(
                track=result,
                provider_name=self.provider_name,
                assets=assets
            ) for result, assets in zip(results, assets_list)
        ]

        return Collection(
            items=mapped_results
        )