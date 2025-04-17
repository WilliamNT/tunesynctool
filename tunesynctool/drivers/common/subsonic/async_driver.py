from tunesynctool.models import Configuration
from tunesynctool.drivers import AsyncWrappedServiceDriver, ServiceDriver
from .driver import SubsonicDriver

class AsyncSubsonicDriver(AsyncWrappedServiceDriver):
    def __init__(self, config: Configuration):
        super().__init__(
            sync_driver=SubsonicDriver(
                config=config
            )
        )