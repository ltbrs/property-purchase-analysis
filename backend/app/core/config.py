from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Property Purchase Analysis API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:3000"

    database_url: str | None = None
    object_storage_endpoint: str | None = None
    object_storage_bucket: str | None = None
    object_storage_access_key: SecretStr | None = None
    object_storage_secret_key: SecretStr | None = None
    llm_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
