from tunesynctool.models import Configuration
from tunesynctool.drivers import AsyncWrappedServiceDriver, ServiceDriver
from .driver import YouTubeDriver

class AsyncYouTubeDriver(AsyncWrappedServiceDriver):
    def __init__(self, config: Configuration):
        super().__init__(
            sync_driver=YouTubeDriver(
                config=config
            )
        )