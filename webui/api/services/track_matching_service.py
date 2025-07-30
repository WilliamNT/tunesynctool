from typing import Annotated
from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.features.async_track_matcher import AsyncTrackMatcher
from tunesynctool.models import Track
import uuid
from fastapi import Depends, HTTPException

from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.services.service_driver_helper_service import ServiceDriverHelperService, get_service_driver_helper_service
from api.models.track import TrackRead, TrackMatchCreate
from api.models.search import SearchParamsBase
from api.core.logging import logger
from api.helpers.mapping import map_track_between_domain_model_and_response_model

class TrackMatchingService:
    """
    Handles track matching operations.
    """

    def __init__(self, auth_service: AuthService, credentials_service: CredentialsService, service_driver_helper_service: ServiceDriverHelperService) -> None:
        self.auth_service = auth_service
        self.credentials_service = credentials_service
        self.service_driver_helper_service = service_driver_helper_service

    async def handle_matching(self, jwt: str, search_params: SearchParamsBase, reference_metadata: TrackMatchCreate) -> TrackRead:
        """
        Handles the track matching process.
        """
        user = await self.auth_service.resolve_user_from_jwt(jwt)
        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=search_params.provider,
        )

        if not credentials:
            logger.warning(f"User {user.id} does not have credentials for provider \"{search_params.provider}\" but wanted to match a track anyway.")
            self.raise_missing_or_invalid_auth_credentials_exception(search_params.provider)

        try:
            driver = await self.service_driver_helper_service.get_initialized_driver(
                credentials=credentials,
                provider_name=search_params.provider,
                user=user
            )
        except ValueError:
            self.raise_unsupported_provider_exception(
                provider_name=search_params.provider
            )

        return await self.find_match(
            service_driver=driver,
            search_params=search_params,
            reference_metadata=reference_metadata
        )

    async def find_match(self, service_driver: AsyncWrappedServiceDriver, search_params: SearchParamsBase, reference_metadata: TrackMatchCreate) -> TrackRead:
        """
        Finds a match for the given track metadata.
        """

        matcher = AsyncTrackMatcher(
            target_driver=service_driver
        )

        reference_mapped_track = Track(
            title=reference_metadata.title,
            album_name=reference_metadata.album_name,
            primary_artist=reference_metadata.author.primary,
            additional_artists=reference_metadata.author.collaborating,
            duration_seconds=reference_metadata.duration,
            track_number=reference_metadata.track_number,
            isrc=reference_metadata.identifiers.isrc,
            musicbrainz_id=reference_metadata.identifiers.musicbrainz,
            service_name=uuid.uuid4().hex,
            service_data=None
        )
        
        most_likely_match = await matcher.find_match(
            track=reference_mapped_track
        )

        if not most_likely_match:
            raise HTTPException(
                status_code=404,
                detail="Couldn't find a close enough match."
            )

        return map_track_between_domain_model_and_response_model(
            track=most_likely_match,
            provider_name=search_params.provider,
            assets=None
        )
    
def get_track_matching_service(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    service_driver_helper_service: Annotated[ServiceDriverHelperService, Depends(get_service_driver_helper_service)]
) -> TrackMatchingService:
    
    return TrackMatchingService(
        auth_service=auth_service,
        credentials_service=credentials_service,
        service_driver_helper_service=service_driver_helper_service
    )