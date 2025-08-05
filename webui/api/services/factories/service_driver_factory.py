from typing import Union
from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.models import Configuration
from google.oauth2.credentials import Credentials as GoogleCredentials
from fastapi import HTTPException
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler

from api.models.service import ServiceCredentials
from api.core.config import config
from api.helpers.service_driver import get_driver_by_name
from api.core.logging import logger
from api.core.config import config
from api.services.credentials_service import CredentialsService
from api.models.user import User
from api.helpers.ytmusicapi import CustomYTMusicAPIOAuthCredentials
from api.exceptions.auth import OAuthTokenRefreshError
from api.drivers.cached.async_cached_driver import AsyncCachedDriver

class ServiceDriverFactory:
    """
    Includes methods to initialize service drivers.
    """

    def __init__(self, provider_name: str, credentials_service: CredentialsService) -> None:
        self.provider_name = provider_name
        self.credentials_service = credentials_service

    async def create(self, user: User) -> AsyncWrappedServiceDriver:
        """
        Returns a ready to use AsyncWrappedServiceDriver implementation for the specified provider.
        """

        credentials = await self.credentials_service.get_service_credentials(
            user=user,
            service_name=self.provider_name
        )

        try:
            config: Union[Configuration | GoogleCredentials | SpotifyOAuth | CustomYTMusicAPIOAuthCredentials] = await self._get_config(
                credentials=credentials,
                user=user
            )
        except ValueError:
            logger.error(f"Attempted to resolve non-existent service driver: {self.provider_name}")
            raise

        driver: AsyncWrappedServiceDriver = get_driver_by_name(self.provider_name)
        
        match self.provider_name:
            case "youtube":
                return AsyncCachedDriver(driver(
                    config=Configuration(),
                    oauth_credentials=config,
                    auth_dict=config.custom_get_auth_dict()
                ))
            case "spotify":
                return AsyncCachedDriver(driver(
                    config=Configuration(),
                    auth_manager=config
                ))
            case _:
                return AsyncCachedDriver(driver(
                    config=config
                ))

    async def _get_config(self, user: User, credentials: ServiceCredentials) -> Configuration:
        match self.provider_name:
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
                raise ValueError(f"Unsupported provider: {self.provider_name}")

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
    
    async def _get_youtube_config(self, user: User, credentials: ServiceCredentials) -> CustomYTMusicAPIOAuthCredentials:
        try:
            fresh_credentials = await self.credentials_service.refresh_google_credentials(
                user=user,
                credentials=credentials
            )
        except OAuthTokenRefreshError:
            private_reason = "Credentials were invalid, have expired or the user revoked access and could not be refreshed."
            await self.credentials_service.delete_credentials(
                user=user,
                service_name=credentials.service_name,
                log_reason=private_reason
            )

            raise HTTPException(
                status_code=403,
                detail=private_reason + " Relinking will likely fix this issue."
            )

        google_credentials = GoogleCredentials.from_authorized_user_info(
            info=fresh_credentials.credentials,
            scopes=config.GOOGLE_SCOPES
        )

        ytmusicapi_credentials = CustomYTMusicAPIOAuthCredentials(
            client_id=config.GOOGLE_CLIENT_ID,
            client_secret=config.GOOGLE_CLIENT_SECRET,
            google_credentials=google_credentials
        )

        return ytmusicapi_credentials
    
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