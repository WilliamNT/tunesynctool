from dataclasses import dataclass, field
from typing import List, Optional
import os

@dataclass(frozen=True)
class Configuration:
    """Single source of truth for configuration parameters."""

    spotify_client_id: str = field(default=None)
    """
    Spotify client ID. Required for Spotify API access.

    Learn more: https://developer.spotify.com/documentation/web-api/concepts/apps
    """

    spotify_client_secret: str = field(default=None)
    """
    Spotify client secret. Required for Spotify API access.

    Learn more: https://developer.spotify.com/documentation/web-api/concepts/apps
    """

    spotify_redirect_uri: str = field(default='http://localhost:8888/callback')
    """
    Spotify redirect URI. Required for Spotify API access.

    Learn more: https://developer.spotify.com/documentation/web-api/concepts/apps
    """

    spotify_scopes: str = field(default='user-library-read,playlist-read-private,playlist-read-collaborative,playlist-modify-public,playlist-modify-private')
    """
    A list of Spotify scopes, seperated with commas. Required for Spotify API access. You can override this, but shouldn't unless you know what you're doing.
    If changed, make sure to reauthenticate.

    Learn more: https://developer.spotify.com/documentation/web-api/concepts/scopes
    """

    subsonic_base_url: str = field(default="http://127.0.0.1")
    """
    Base URL for the Subsonic server. Required for Subsonic API access.
    Should include the protocol (http/https) and the domain or IP address.
    A valid value for example would be "https://demo.subsonic.org" or "http://192.168.1.2".
    """

    subsonic_port: int = field(default=4533)
    """
    Port for the Subsonic server. Required for Subsonic API access.
    """

    subsonic_username: str = field(default=None)
    """
    Username for the Subsonic server. Required for Subsonic API access.
    """

    subsonic_password: str = field(default=None)
    """
    Password for the Subsonic server. Required for Subsonic API access.
    """

    subsonic_legacy_auth: bool = field(default=False)
    """
    Enable legacy auth for Subsonic server. Required for some servers to authenticate.
    """

    deezer_arl: Optional[str] = field(default=None)
    """
    Deezer ARL token. Required for Deezer API access.
    """

    youtube_request_headers: Optional[str] = field(default=None)
    """
    Raw request headers from any authenticated request sent from your browser of choice to music.youtube.com.

    Learn more and how to obtain: https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html
    """

    @classmethod
    def from_env(cls) -> 'Configuration':
        """Create a Configuration instance from environment variables."""

        try:
            config = cls(
                spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                spotify_redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", cls.spotify_redirect_uri),
                spotify_scopes=os.getenv("SPOTIFY_SCOPES", cls.spotify_scopes),
                subsonic_base_url=os.getenv("SUBSONIC_BASE_URL", cls.subsonic_base_url),
                subsonic_port=int(os.getenv("SUBSONIC_PORT", cls.subsonic_port)),
                subsonic_username=os.getenv("SUBSONIC_USERNAME"),
                subsonic_password=os.getenv("SUBSONIC_PASSWORD"),
                subsonic_legacy_auth=os.getenv("SUBSONIC_LEGACY_AUTH", False),
                deezer_arl=os.getenv("DEEZER_ARL"),
                youtube_request_headers=os.getenv("YOUTUBE_REQUEST_HEADERS")
            )

            return config
        except KeyError as e:
            raise ValueError(f"Missing required environment variable: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid configuration value: {e}")