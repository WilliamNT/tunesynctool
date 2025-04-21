from datetime import datetime, timezone
from ytmusicapi import OAuthCredentials
from ytmusicapi.auth.oauth.models import BaseTokenDict
from google.oauth2.credentials import Credentials as GoogleCredentials

from api.core.config import config

class CustomYTMusicAPIOAuthCredentials(OAuthCredentials):
    def __init__(self, client_id: str, client_secret: str, google_credentials: GoogleCredentials):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            proxies=None,
            session=None
        )

        self.google_credentials = google_credentials

    def get_code(self):
        return None
    
    def refresh_token(self, refresh_token: str):
        expiry = self.google_credentials.expiry

        # If expiry is naive, assume it's in UTC and make it aware
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        expires_in_seconds = (expiry - datetime.now(timezone.utc)).total_seconds()
        expires_in_seconds = max(0, expires_in_seconds)
        
        return BaseTokenDict(
            access_token=self.google_credentials.token,
            refresh_token=self.google_credentials.refresh_token,
            expires_in=expires_in_seconds,
            scope=config.GOOGLE_SCOPES[0]
        )
    
    def custom_get_auth_dict(self) -> dict:
        return {
            "access_token": self.google_credentials.token,
            "refresh_token": self.google_credentials.refresh_token,
            "token_type": "Bearer",
            "scope": config.GOOGLE_SCOPES[0],
        }
    