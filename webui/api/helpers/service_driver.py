from tunesynctool.drivers import (
    AsyncWrappedServiceDriver,
    AsyncDeezerDriver,
    AsyncSpotifyDriver,
    AsyncSubsonicDriver,
    AsyncYouTubeDriver
)

from api.drivers.youtube import AsyncYouTubeOAuth2Driver

DRIVERS = {
    "spotify": AsyncSpotifyDriver,
    "youtube": AsyncYouTubeDriver,
    "subsonic": AsyncSubsonicDriver,
    "deezer": AsyncDeezerDriver,
}

SUPPORTED_PROVIDERS = list(DRIVERS.keys())

def is_valid_provider(name: str) -> bool:
    """
    Check if a provider is valid. Is case insensitive.

    :param name: The name of the provider.
    :return: True if the provider is valid, False otherwise.
    """

    return name.lower().strip() in SUPPORTED_PROVIDERS

def get_driver_by_name(name: str) -> AsyncWrappedServiceDriver:
    """
    Get a driver class by its name.

    :param name: The name of the driver.
    :return: The driver class.
    """

    try:
        return DRIVERS[name]
    except KeyError:
        raise ValueError(f"Driver '{name}' does not exist. Supported drivers are: {', '.join(SUPPORTED_PROVIDERS)}")
    