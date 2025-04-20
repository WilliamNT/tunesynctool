from tunesynctool.models import Configuration
from tunesynctool.drivers import AsyncWrappedServiceDriver
from .driver import SpotifyDriver

from spotipy.oauth2 import SpotifyOAuth

class AsyncSpotifyDriver(AsyncWrappedServiceDriver):
    def __init__(self, config: Configuration, auth_manager: SpotifyOAuth):
        super().__init__(
            sync_driver=SpotifyDriver(
                config=config,
                auth_manager=auth_manager
            )
        )