from dataclasses import dataclass, field
from typing import List, Optional
import os

@dataclass(frozen=True)
class Configuration:
    """Single source of truth for configuration parameters."""

    spotify_client_id: str = field(default=None)
    spotify_client_secret: str = field(default=None)
    spotify_redirect_uri: str = field(default='http://localhost:8888/callback')
    spotify_scopes: str = field(default='user-library-read,playlist-read-private,playlist-read-collaborative,playlist-modify-public,playlist-modify-private')
    
    whitelisted_ids: List[str] = field(default_factory=list)
    preview_only: bool = field(default=True)

    subsonic_base_url: str = field(default="http://127.0.0.1")
    subsonic_port: int = field(default=4533)
    subsonic_username: str = field(default=None)
    subsonic_password: str = field(default=None)

    @classmethod
    def from_env(cls) -> 'Configuration':
        """Create a Configuration instance from environment variables."""

        try:
            config = cls(
                spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                spotify_redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", cls.spotify_redirect_uri),
                spotify_scopes=os.getenv("SPOTIFY_SCOPES", cls.spotify_scopes),
                whitelisted_ids=os.getenv("WHITELISTED_IDS", "").split(","),
                preview_only=os.getenv("PREVIEW_ONLY", "true").lower() == "true",
                subsonic_base_url=os.getenv("SUBSONIC_BASE_URL", cls.subsonic_base_url),
                subsonic_port=int(os.getenv("SUBSONIC_PORT", cls.subsonic_port)),
                subsonic_username=os.getenv("SUBSONIC_USERNAME"),
                subsonic_password=os.getenv("SUBSONIC_PASSWORD")
            )
            
            config.validate()

            return config
        except KeyError as e:
            raise ValueError(f"Missing required environment variable: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid configuration value: {e}")

    def validate(self) -> None:
        """Validate configuration values."""
        
        missing_fields = []
        if not self.spotify_client_id:
            missing_fields.append("spotify_client_id")
        if not self.spotify_client_secret:
            missing_fields.append("spotify_client_secret")
        if not self.spotify_redirect_uri:
            missing_fields.append("spotify_redirect_uri")
        if not self.subsonic_username:
            missing_fields.append("subsonic_username")
        if not self.subsonic_password:
            missing_fields.append("subsonic_password")

        if missing_fields:
            raise ValueError(f"Missing required configuration values: {', '.join(missing_fields)}")