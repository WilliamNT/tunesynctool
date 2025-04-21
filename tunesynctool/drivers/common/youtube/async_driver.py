from typing import Optional
from tunesynctool.models import Configuration
from tunesynctool.drivers import AsyncWrappedServiceDriver, ServiceDriver
from .driver import YouTubeDriver

from ytmusicapi import OAuthCredentials

class AsyncYouTubeDriver(AsyncWrappedServiceDriver):
    def __init__(self, config: Configuration, oauth_credentials: Optional[OAuthCredentials] = None, auth_dict: Optional[dict] = None) -> None:
        super().__init__(
            sync_driver=YouTubeDriver(
                config=config,
                oauth_credentials=oauth_credentials,
                auth_dict=auth_dict
            )
        )