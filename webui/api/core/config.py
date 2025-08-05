from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, MySQLDsn
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

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str

    SUBSONIC_BASE_URL: str
    SUBSONIC_PORT: int
    SUBSONIC_LEGACY_AUTH: bool = False

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

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

config = Config()