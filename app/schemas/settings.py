from pydantic import PostgresDsn, SecretStr, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsSchema(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=r"app\.env", env_file_encoding="utf-8"
    )

    DATABASE_URL: PostgresDsn
    DATABASE_PASS: SecretStr
    DATABASE_USR: str

    JWT_SECRET_KEY: SecretStr
    JWT_REFRESH_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: PositiveInt = 15
    REFRESH_TOKEN_EXPIRE_DAYS: PositiveInt = 7

