from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.exceptions import ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException
from tunesynctool.models import Track

from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.logging import logger
from api.models.search import SearchParams, ISRCSearchParams, TrackLookupByIDParams
from api.models.collection import SearchResultCollection
from api.services.auth_service import AuthService, get_auth_service
from api.models.track import TrackRead, TrackArtistsRead, TrackIdentifiersRead, TrackMetaRead
from api.services.service_driver_helper_service import ServiceDriverHelperService, get_service_driver_helper_service

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
            service_driver=driver
        )

        return SearchResultCollection(
            items=results,
            query=search_parameters.query
        )

    async def search(self, search_parameters: SearchParams, service_driver: AsyncWrappedServiceDriver) -> list[TrackRead]:
        try:
            results = await service_driver.search_tracks(
                query=search_parameters.query,
                limit=search_parameters.limit
            )

            mapped_results = []
            for result in results:
                mapped_results.append(self._map_track(
                    track=result,
                    provider_name=search_parameters.provider
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
                
    def _map_track(self, track: Track, provider_name: str) -> TrackRead:
        meta = TrackMetaRead(
            provider_name=provider_name
        )
        
        artists = TrackArtistsRead(
            primary=track.primary_artist,
            collaborating=track.additional_artists
        )

        identifiers = TrackIdentifiersRead(
            provider_id=str(track.service_id),
            musicbrainz=track.musicbrainz_id,
            isrc=track.isrc
        )

        mapped = TrackRead(
            title=track.title,
            album_name=track.album_name,
            duration=track.duration_seconds,
            track_number=track.track_number,
            release_year=track.release_year,
            artists=artists,
            meta=meta,
            identifiers=identifiers,
        )

        return mapped
        
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

    async def handle_track_lookup(self, search_parameters: TrackLookupByIDParams, jwt: str) -> TrackRead:
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
    
    async def track_lookup(self, search_parameters: TrackLookupByIDParams, service_driver: AsyncWrappedServiceDriver) -> TrackRead:
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