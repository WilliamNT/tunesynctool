from typing import Annotated, Union
from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.models import Configuration
from google.oauth2.credentials import Credentials as GoogleCredentials
from fastapi import Depends
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler

from api.models.service import ServiceCredentials
from api.core.config import config
from api.helpers.service_driver import get_driver_by_name
from api.core.logging import logger
from api.core.config import config
from api.services.credentials_service import get_credentials_service, CredentialsService
from api.models.user import User

class ServiceDriverHelperService:
    """
    Provides methods to initialize service drivers.
    """

    def __init__(self, credentials_service: CredentialsService) -> None:
        self.credentials_service = credentials_service

    async def get_initialized_driver(self, user: User, credentials: ServiceCredentials, provider_name: str) -> AsyncWrappedServiceDriver:
        """
        Returns an initialized driver for the specified provider.
        This method retrieves the user's credentials for the specified provider and initializes the driver with those credentials.

        :param user: The user to get the driver for.
        :param provider_name: The name of the provider.
        :return: The initialized driver.
        :raises ValueError: If the provider name is not supported.
        """

        try:
            config: Union[Configuration | GoogleCredentials | SpotifyOAuth] = await self._get_config(
                credentials=credentials,
                provider_name=provider_name,
                user=user
            )
        except ValueError:
            logger.error(f"Attempted to resolve non-existent service driver: {provider_name}")
            raise

        driver: AsyncWrappedServiceDriver = get_driver_by_name(provider_name)

        match provider_name.lower().strip():
            case "youtube":
                return driver(
                    google_credentials=config
                )
            case "spotify":
                return driver(
                    config=Configuration(),
                    auth_manager=config
                )
            case _:
                return driver(
                    config=config
                )

    async def _get_config(self, user: User, credentials: ServiceCredentials, provider_name: str) -> Configuration:
        match provider_name:
            case "deezer":
                return self._get_deezer_config(credentials)
            case "subsonic":
                return self._get_subsonic_config(credentials)
            case "youtube":
                return await self._get_youtube_config(
                    credentials=credentials,
                    user=user
                )
            case "spotify":
                return self._get_spotify_config(credentials)
            case _:
                raise ValueError(f"Unsupported provider: {provider_name}")

    def _get_deezer_config(self, credentials: ServiceCredentials) -> Configuration:
        return Configuration(
            deezer_arl=credentials.credentials.get("arl")
        )
    
    def _get_subsonic_config(self, credentials: ServiceCredentials) -> Configuration:
        return Configuration(
            subsonic_username=credentials.credentials.get("username"),
            subsonic_password=credentials.credentials.get("password"),
            subsonic_base_url=config.SUBSONIC_BASE_URL,
            subsonic_port=config.SUBSONIC_PORT,
            subsonic_legacy_auth=config.SUBSONIC_LEGACY_AUTH
        )
    
    async def _get_youtube_config(self, user: User, credentials: ServiceCredentials) -> GoogleCredentials:
        fresh_credentials = await self.credentials_service.refresh_google_credentials(
            user=user,
            credentials=credentials
        )

        google_credentials = GoogleCredentials.from_authorized_user_info(
            info=fresh_credentials.credentials,
            scopes=config.GOOGLE_SCOPES
        )

        return google_credentials
    
    def _get_spotify_config(self, credentials: ServiceCredentials) -> SpotifyOAuth:
        cache_handler = MemoryCacheHandler(
            token_info=credentials.credentials
        )

        return SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI,
            scope=config.SPOTIFY_SCOPES,
            open_browser=False,
            show_dialog=True,
            cache_path=None,
            cache_handler=cache_handler
        )


def get_service_driver_helper_service(credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]) -> ServiceDriverHelperService:
    return ServiceDriverHelperService(
        credentials_service=credentials_service
    )