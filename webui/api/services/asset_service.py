import hashlib
import random
import string
from typing import Annotated, Optional
from fastapi import Depends
from tunesynctool.drivers.async_service_driver import AsyncWrappedServiceDriver
from tunesynctool.models.track import Track

from api.services.auth_service import AuthService, get_auth_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.services.service_driver_helper_service import ServiceDriverHelperService, get_service_driver_helper_service
from api.models.service import ServiceCredentials
from api.helpers.extraction import extract_cover_link_for_track_sync
from api.models.entity import EntityAssetsBase
from api.models.search import LookupByProviderIDParams
from api.core.logging import logger
from api.core import config
from api.models.user import User

class AssetService:
    """
    Encapsulates various asset fetching tasks for playlists and tracks.
    """

    def __init__(self, auth_service: AuthService, credentials_service: CredentialsService, service_driver_helper_service: ServiceDriverHelperService) -> None:
        self.auth_service = auth_service
        self.credentials_service = credentials_service
        self.service_driver_helper_service = service_driver_helper_service

    async def fetch_track_assets(self, service_driver: AsyncWrappedServiceDriver, search_parameters: LookupByProviderIDParams, credentials: ServiceCredentials) -> EntityAssetsBase:
        track = await service_driver.get_track(
            track_id=search_parameters.provider_id
        )

        link = None
        extra_data = track.service_data

        sync_extractables = ["spotify", "youtube", "deezer"]
        if track.service_name in sync_extractables:
            link = extract_cover_link_for_track_sync(partial_data=extra_data, provider_name=track.service_name)
        elif track.service_name == "subsonic":
            link = await self._get_subsonic_cover_art(track=track, credentials=credentials)
        else:
            raise ValueError(f"Invalid service name was specified in Track.service_name. \"{track.service_name}\" is not recognized. Was a custom track object somehow passed to this function?")

        return EntityAssetsBase(
            cover_image=link
        )

    async def get_track_assets(self, search_parameters: LookupByProviderIDParams, user: User, credentials: Optional[ServiceCredentials] = None) -> EntityAssetsBase:
        if not credentials:
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

        return await self.fetch_track_assets(
            service_driver=driver,
            search_parameters=search_parameters,
            credentials=credentials
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

def get_asset_service(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
    service_driver_helper_service: Annotated[ServiceDriverHelperService, Depends(get_service_driver_helper_service)]
) -> AssetService:
    
    return AssetService(
        auth_service=auth_service,
        credentials_service=credentials_service,
        service_driver_helper_service=service_driver_helper_service
    )