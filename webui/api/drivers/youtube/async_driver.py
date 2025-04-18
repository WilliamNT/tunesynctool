from tunesynctool.drivers import AsyncWrappedServiceDriver
from google.oauth2.credentials import Credentials as GoogleCredentials

from .driver import YouTubeOAuth2Driver

class AsyncYouTubeOAuth2Driver(AsyncWrappedServiceDriver):
    def __init__(self, google_credentials: GoogleCredentials):
        super().__init__(
            sync_driver=YouTubeOAuth2Driver(
                google_credentials=google_credentials
            )
        )