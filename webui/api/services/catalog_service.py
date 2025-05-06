from typing import Annotated, Optional
import random
import string
import hashlib

from fastapi import Depends, HTTPException
from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.exceptions import ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException, PlaylistNotFoundException
from tunesynctool.models import Track, Playlist

from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.logging import logger
from api.models.search import SearchParams, ISRCSearchParams, LookupByProviderIDParams, LookupLibraryPlaylistsParams, SearchParamsBase
from api.models.collection import SearchResultCollection, Collection
from api.services.auth_service import AuthService, get_auth_service
from api.models.track import TrackAssetsRead, TrackRead, TrackIdentifiersRead
from api.models.entity import EntityMetaRead, EntityMultiAuthorRead, EntitySingleAuthorRead, EntityIdentifiersBase
from api.services.service_driver_helper_service import ServiceDriverHelperService, get_service_driver_helper_service
from api.models.playlist import PlaylistRead, PlaylistCreate, PlaylistMultiTrackInsert
from api.core.config import config
from api.models.service import ServiceCredentials

class CatalogService:
    """
    Handles catalog operations.

    Provides an asynchronous abstraction for the tunesynctool package.
    """

    def __init__(self, credentials_service: CredentialsService, auth_service: AuthService, service_driver_helper_service: ServiceDriverHelperService) -> None:
        self.credentials_service = credentials_service
        self.auth_service = auth_service
        self.service_driver_helper_service = service_driver_helper_service
        
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
            self.raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
                provider_name=search_parameters.provider
            )

        results = await self.search(
            search_parameters=search_parameters,
            service_driver=driver,
            credentials=credentials
        )

        return SearchResultCollection(
            items=results,
            query=search_parameters.query
        )

    async def search(self, search_parameters: SearchParams, service_driver: AsyncWrappedServiceDriver, credentials: ServiceCredentials) -> list[TrackRead]:
        try:
            results = await service_driver.search_tracks(
                query=search_parameters.query,
                limit=search_parameters.limit
            )

            if len(results) > search_parameters.limit:
                results = results[:search_parameters.limit]

            mapped_results = []
            for result in results:
                if len(mapped_results) > 1:
                    break
                mapped_results.append(await self._map_track(
                    track=result,
                    provider_name=search_parameters.provider,
                    credentials=credentials
                ))

            return mapped_results
        except UnsupportedFeatureException as e:
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            self.raise_service_driver_generic_exception(
                provider_name=search_parameters.provider,
                e=e
            )
                
    async def _map_track(self, track: Track, provider_name: str, credentials: ServiceCredentials) -> TrackRead:
        meta = EntityMetaRead(
            provider_name=provider_name
        )
        
        artists = EntityMultiAuthorRead(
            primary=track.primary_artist,
            collaborating=track.additional_artists
        )

        identifiers = TrackIdentifiersRead(
            provider_id=str(track.service_id),
            musicbrainz=track.musicbrainz_id,
            isrc=track.isrc
        )

        assets = await self._map_track_assets(track=track, credentials=credentials)

        mapped = TrackRead(
            title=track.title,
            album_name=track.album_name,
            duration=track.duration_seconds,
            track_number=track.track_number,
            release_year=track.release_year,
            author=artists,
            meta=meta,
            identifiers=identifiers,
            assets=assets
        )

        return mapped
        
    async def _map_track_assets(self, track: Track, credentials: ServiceCredentials) -> TrackRead:
        link = None
        extra_data = track.service_data

        match track.service_name:
            case "spotify":
                link = extra_data.get("album", {}).get("images", [])[0].get("url", None)
            case "youtube":
                link = extra_data.get("track", {}).get("videoDetails", {}).get("thumbnail", {}).get("thumbnails", [])[0].get("url", None)
            case "deezer":
                link = extra_data.get("album", {}).get("cover", None)
            case "subsonic":
                link = await self._get_subsonic_cover_art(track=track, credentials=credentials)

        return TrackAssetsRead(
            cover_image=link
        )

    async def _get_subsonic_cover_art(self, track: Track, credentials: ServiceCredentials) -> Optional[str]:
        """
        Get the cover art URL for a track from Subsonic.
        """
        if not track.service_data:
            return None

        cover_art = track.service_data.get("coverArt", None)
        if not cover_art:
            return None
        
        password = credentials.credentials.get("password")
        if not password:
            logger.error(f"User {credentials.user_id} does not have a password for Subsonic but still we fetched from the API successfully. This is likely a bug..")
            return None
        
        username = credentials.credentials.get("username")
        if not username:
            logger.error(f"User {credentials.user_id} does not have a username for Subsonic but still we fetched from the API successfully. This is likely a bug..")
            return None

        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        token_input = password + salt
        token = hashlib.md5(token_input.encode('utf-8')).hexdigest()

        return f"{config.SUBSONIC_BASE_URL}:{config.SUBSONIC_PORT}/rest/getCoverArt.view?id={cover_art}&s={salt}&t={token}&u={username}&v=1.8.0&c=tunesynctool&f=json"

    def raise_missing_or_invalid_auth_credentials_exception(self, provider_name: str) -> None:
        """
        Raises an HTTPException with a 400 status code and a message indicating that the catalog operation failed due to user error.
        """
        
        raise HTTPException(
            status_code=401,
            detail=f"Missing or invalid credentials for provider \"{provider_name}\". If \"{provider_name}\" is an OAuth provider, authorization is required. Otherwise, please set the proper credentials.",
        )   

    def raise_unsupported_driver_feature_exception(self, provider_name: str, e: Optional[Exception] = None) -> None:
        logger.warning(f"Provider \"{provider_name}\" does not support a feature but it was called anyway{": " + str(e) if e else "."}")

        msg = f"Provider \"{provider_name}\" does not support this feature."
        code = 400

        if e:
            raise HTTPException(
                status_code=code,
                detail=msg,
            ) from e
            
        raise HTTPException(
            status_code=code,
            detail=msg,
        )

    def raise_service_driver_generic_exception(self, provider_name: str, e: Optional[Exception] = None) -> None:
        logger.error(f"Service driver error: {e}")

        msg = f"Provider \"{provider_name}\" returned an error."
        code = 400

        if e:
            raise HTTPException(
                status_code=code,
                detail=msg,
            ) from e
        
        raise HTTPException(
            status_code=code,
            detail=msg,
        )

    def raise_unsupported_provider_exception(self, provider_name: str) -> None:
        logger.warning(f"Provider \"{provider_name}\" is not supported.")

        raise HTTPException(
            status_code=400,
            detail=f"Provider \"{provider_name}\" is not supported.",
        )

    async def handle_isrc_search(self, search_parameters: ISRCSearchParams, jwt: str) -> TrackRead:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to look a track up by its ISRC anyway.")
            self.raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
                provider_name=search_parameters.provider
            )

        return await self.search_isrc(
            search_parameters=search_parameters,
            service_driver=driver
        )
    
    async def search_isrc(self, search_parameters: ISRCSearchParams, service_driver: AsyncWrappedServiceDriver) -> TrackRead:
        if not service_driver.supports_direct_isrc_querying:
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider
            )
            
        try:
            result = await service_driver.get_track_by_isrc(
                isrc=search_parameters.isrc
            )

            return self._map_track(
                track=result,
                provider_name=search_parameters.provider
            )
        except UnsupportedFeatureException as e:
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            self.raise_service_driver_generic_exception(
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
            self.raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
                provider_name=search_parameters.provider
            )

        return await self.track_lookup(
            search_parameters=search_parameters,
            service_driver=driver
        )
    
    async def track_lookup(self, search_parameters: LookupByProviderIDParams, service_driver: AsyncWrappedServiceDriver) -> TrackRead:
        try:
            result = await service_driver.get_track(
                track_id=search_parameters.provider_id
            )

            return self._map_track(
                track=result,
                provider_name=search_parameters.provider
            )
        except UnsupportedFeatureException as e:
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            self.raise_service_driver_generic_exception(
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
            self.raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
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
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            self.raise_service_driver_generic_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except PlaylistNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail=f"Playlist not found.",
            ) from e
        
    def _map_playlist(self, playlist: Playlist, provider_name: str) -> PlaylistRead:
        meta = EntityMetaRead(
            provider_name=provider_name
        )

        author = EntitySingleAuthorRead(
            primary=playlist.author_name
        )

        identifiers = EntityIdentifiersBase(
            provider_id=str(playlist.service_id)
        )

        return PlaylistRead(
            title=playlist.name,
            description=playlist.description,
            is_public=playlist.is_public,
            author=author,
            meta=meta,
            identifiers=identifiers,
        )
    
    async def handle_playlist_tracks_lookup(self, search_parameters: LookupByProviderIDParams, jwt: str) -> Collection[TrackRead]:
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_parameters.provider,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_parameters.provider}\" but wanted to look a playlist's tracks up by its ID anyway.")
            self.raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
                provider_name=search_parameters.provider
            )

        return await self.playlist_tracks_lookup(
            search_parameters=search_parameters,
            service_driver=driver
        )

    async def playlist_tracks_lookup(self, search_parameters: LookupByProviderIDParams, service_driver: AsyncWrappedServiceDriver) -> Collection[TrackRead]:
        try:
            results = await service_driver.get_playlist_tracks(
                playlist_id=search_parameters.provider_id,
                limit=0
            )

            mapped_results = []
            for result in results:
                mapped_results.append(self._map_track(
                    track=result,
                    provider_name=search_parameters.provider
                ))

            return Collection(
                items=mapped_results
            )
        except UnsupportedFeatureException as e:
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            self.raise_service_driver_generic_exception(
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
            self.raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
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
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            self.raise_service_driver_generic_exception(
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
            self.raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
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
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            self.raise_service_driver_generic_exception(
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
            self.raise_missing_or_invalid_auth_credentials_exception(search_parameters.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_parameters.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
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
            self.raise_unsupported_driver_feature_exception(
                provider_name=search_parameters.provider,
                e=e
            )
        except ServiceDriverException as e:
            self.raise_service_driver_generic_exception(
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
) -> CatalogService:
    return CatalogService(
        auth_service=auth_service,
        credentials_service=credentials_service,
        service_driver_helper_service=service_driver_helper_service,
    )