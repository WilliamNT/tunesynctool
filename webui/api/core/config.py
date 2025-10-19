from typing import List, Optional, Self
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, MySQLDsn, model_validator
from tunesynctool.models.configuration import Configuration as TUNESYNCTOOL_CONFIG

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DB_HOST: str
    DB_PORT: int = 3306
    DB_NAME: str = ""
    DB_USER: str
    DB_PASSWORD: str = ""
    APP_HOST: str
    APP_SECRET: str
    API_BASE_URL: str = "/api"
    ADMIN_PASSWORD: str = "changeme"

    ENCRYPTION_KEY: str
    ENCRYPTION_SALT: str

    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None

    @computed_field
    @property
    def DISABLE_SPOTIFY_PROVIDER(self) -> bool:
        try:
            return not self.validate_dependant_fields(
                fields=[self.SPOTIFY_CLIENT_ID, self.SPOTIFY_CLIENT_SECRET],
                group_name="Spotify"
            )
        except ValueError:
            return True
        
    SUBSONIC_BASE_URL: Optional[str] = None
    SUBSONIC_PORT: Optional[int] = None
    SUBSONIC_LEGACY_AUTH: bool = False

    @computed_field
    @property
    def DISABLE_SUBSONIC_PROVIDER(self) -> bool:
        try:
            return not self.validate_dependant_fields(
                fields=[self.SUBSONIC_BASE_URL, self.SUBSONIC_PORT],
                group_name="Subsonic"
            )
        except ValueError:
            return True

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    @computed_field
    @property
    def DISABLE_GOOGLE_PROVIDER(self) -> bool:
        try:
            return not self.validate_dependant_fields(
                fields=[self.GOOGLE_CLIENT_ID, self.GOOGLE_CLIENT_SECRET],
                group_name="Google OAuth2 credentials"
            )
        except ValueError:
            return True

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MySQLDsn:
        return MultiHostUrl.build(
            scheme="mysql+aiomysql",
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
            username=self.DB_USER,
            password=self.DB_PASSWORD
        )
    
    @computed_field
    @property
    def SPOTIFY_REDIRECT_URI(self) -> str:
        return f"{self.APP_HOST}{self.API_BASE_URL}/providers/spotify/callback"

    @computed_field
    @property
    def SPOTIFY_SCOPES(self) -> str:
        return TUNESYNCTOOL_CONFIG.spotify_scopes
    
    @computed_field
    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        return f"{self.APP_HOST}{self.API_BASE_URL}/providers/youtube/callback"
    
    @computed_field
    @property
    def GOOGLE_SCOPES(self) -> list[str]:
        return [
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.force-ssl"
        ]
    
    def validate_dependant_fields(self, fields: List[str | None], group_name: str) -> bool:
        filled = [f for f in fields if f not in (None, "")]

        if 0 < len(filled) < len(fields):
            raise ValueError(f"{group_name} was/were only partially configured. Not all required configuration values for it/them were set up properly. Related features may be disabled.")

        return len(filled) != 0

    @model_validator(mode="after")
    def verify_spotify_fields(self) -> Self:
        self.validate_dependant_fields(
            fields=[self.SPOTIFY_CLIENT_ID, self.SPOTIFY_CLIENT_SECRET],
            group_name="Spotify"
        )

        return self
    
    @model_validator(mode="after")
    def verify_subsonic_fields(self) -> Self:
        # leaving out self.SUBSONIC_LEGACY_AUTH because it is set to False by default
        self.validate_dependant_fields(
            fields=[self.SUBSONIC_BASE_URL, self.SUBSONIC_PORT],
            group_name="Subsonic"
        )

        return self
    
    @model_validator(mode="after")
    def verify_google_fields(self) -> Self:
        self.validate_dependant_fields(
            fields=[self.GOOGLE_CLIENT_ID, self.GOOGLE_CLIENT_SECRET],
            group_name="Google OAuth2 credentials"
        )
    
        return self

config = Config()
