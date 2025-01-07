from tunesynctool.drivers import *

DRIVERS = {
    'spotify': SpotifyDriver,
    'youtube': YouTubeDriver,
    'subsonic': SubsonicDriver,
    'deezer': DeezerDriver,
}

SUPPORTED_PROVIDERS = list(DRIVERS.keys())

def get_driver_by_name(name: str) -> ServiceDriver:
    """Get a driver class by its name."""

    return DRIVERS[name]