from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.models import Configuration
from google.oauth2.credentials import Credentials as GoogleCredentials

from api.models.service import ServiceCredentials
from api.core.config import config
from api.helpers.service_driver import get_driver_by_name
from api.core.logging import logger
from api.core.config import config

class ServiceDriverHelperService:
    """
    Provides methods to initialize service drivers.
    """

    async def get_initialized_driver(self, credentials: ServiceCredentials, provider_name: str) -> AsyncWrappedServiceDriver:
        """
        Returns an initialized driver for the specified provider.
        This method retrieves the user's credentials for the specified provider and initializes the driver with those credentials.

        :param user: The user to get the driver for.
        :param provider_name: The name of the provider.
        :return: The initialized driver.
        :raises ValueError: If the provider name is not supported.
        """

        try:
            config = self._get_config(
                credentials=credentials,
                provider_name=provider_name
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
                logger.warning("Spotify driver is not implemented yet.")
                pass
            case _:
                return driver(
                    config=config
                )

    def _get_config(self, credentials: ServiceCredentials, provider_name: str) -> Configuration:
        match provider_name:
            case "deezer":
                return self._get_deezer_config(credentials)
            case "subsonic":
                return self._get_subsonic_config(credentials)
            case "youtube":
                return self._get_youtube_config(credentials)
            case "spotify":
                pass
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
    
    def _get_youtube_config(self, credentials: ServiceCredentials) -> GoogleCredentials:
        return GoogleCredentials.from_authorized_user_info(
            info=credentials.credentials,
            scopes=config.GOOGLE_SCOPES
        )

def get_service_driver_helper_service() -> ServiceDriverHelperService:
    return ServiceDriverHelperService()