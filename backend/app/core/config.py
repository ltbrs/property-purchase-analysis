from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPOSITORY_ROOT / ".env", REPOSITORY_ROOT / "backend" / ".env"),
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
    object_storage_region: str = "eu-west-3"
    object_storage_access_key: SecretStr | None = None
    object_storage_secret_key: SecretStr | None = None
    max_upload_size_bytes: int = 25 * 1024 * 1024
    llm_api_key: SecretStr | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def use_psycopg_three_driver(cls, value: object) -> object:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
