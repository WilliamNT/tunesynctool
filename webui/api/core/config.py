from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, MySQLDsn

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DB_HOST: str
    DB_PORT: int = 3306
    DB_NAME: str = ""
    DB_USER: str
    DB_PASSWORD: str = ""
    APP_SECRET: str
    API_BASE_URL: str = "/api"
    ADMIN_PASSWORD: str = "admin"

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

config = Config()