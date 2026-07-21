from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsSchema(BaseSettings):
    model_config = SettingsConfigDict(env_file=r"app\.env", env_file_encoding="utf-8")

    DATABASE_URL: PostgresDsn
    DATABASE_PASS: SecretStr
    DATABASE_USR: str
    CORS_ALLOWED_ORIGINS: list[str]
    CORS_ALLOWED_METHODS: list[str]
