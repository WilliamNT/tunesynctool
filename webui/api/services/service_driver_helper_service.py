from tunesynctool.drivers import ServiceDriver
from tunesynctool.models import Configuration

from api.models.user import User
from api.models.service import ServiceCredentials
from api.core.config import config
from api.helpers.service_driver import get_driver_by_name

class ServiceDriverHelperService:
    """
    Provides methods to initialize service drivers.
    """

    async def get_initialized_driver(self, user: User, credentials: ServiceCredentials, provider_name: str) -> ServiceDriver:
        """
        Returns an initialized driver for the specified provider.
        This method retrieves the user's credentials for the specified provider and initializes the driver with those credentials.

        :param user: The user to get the driver for.
        :param provider_name: The name of the provider.
        :return: The initialized driver.
        """

        config = self._get_config(
            credentials=credentials,
            provider_name=provider_name
        )

        driver: ServiceDriver = get_driver_by_name(provider_name)

        return driver(config)

    def _get_config(self, credentials: ServiceCredentials, provider_name: str) -> Configuration:
        match provider_name:
            case "deezer":
                return self._get_deezer_config(credentials)
            case "subsonic":
                return self._get_subsonic_config(credentials)
            case "youtube", "spotify":
                pass

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

def get_service_driver_helper_service() -> ServiceDriverHelperService:
    return ServiceDriverHelperService()