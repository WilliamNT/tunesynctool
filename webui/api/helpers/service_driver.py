from tunesynctool.drivers import *

DRIVERS = {
    "spotify": SpotifyDriver,
    "youtube": YouTubeDriver,
    "subsonic": SubsonicDriver,
    "deezer": DeezerDriver,
}

SUPPORTED_PROVIDERS = list(DRIVERS.keys())

def is_valid_provider(name: str) -> bool:
    """
    Check if a provider is valid. Is case insensitive.

    :param name: The name of the provider.
    :return: True if the provider is valid, False otherwise.
    """

    return name.lower().strip() in SUPPORTED_PROVIDERS

def get_driver_by_name(name: str) -> ServiceDriver:
    """
    Get a driver class by its name.

    :param name: The name of the driver.
    :return: The driver class.
    """

    try:
        return DRIVERS[name]
    except KeyError:
        raise ValueError(f"Driver '{name}' does not exist. Supported drivers are: {', '.join(SUPPORTED_PROVIDERS)}")
    