from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPOSITORY_ROOT / ".env", REPOSITORY_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Property Purchase Analysis API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:3000"

    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "DATABASE_URL",
            "POSTGRES_URL",
            "POSTGRES_URL_NON_POOLING",
        ),
    )
    object_storage_endpoint: str | None = None
    object_storage_bucket: str | None = None
    object_storage_region: str = "eu-west-3"
    object_storage_access_key: SecretStr | None = None
    object_storage_secret_key: SecretStr | None = None
    document_view_url_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    max_upload_size_bytes: int = 25 * 1024 * 1024
    openai_api_key: SecretStr | None = None
    ademe_dpe_api_url: str = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant"
    ademe_dpe_api_timeout_seconds: float = Field(default=5, gt=0, le=30)
    contact_proxy_secret: SecretStr | None = None
    backend_proxy_secret: SecretStr | None = None
    contact_short_rate_limit: int = Field(default=5, ge=1, le=100)
    contact_daily_rate_limit: int = Field(default=20, ge=1, le=1000)

    @field_validator("database_url", mode="before")
    @classmethod
    def use_psycopg_three_driver(cls, value: object) -> object:
        if isinstance(value, str):
            for scheme in ("postgresql://", "postgres://"):
                if value.startswith(scheme):
                    return value.replace(scheme, "postgresql+psycopg://", 1)
        return value

    @field_validator(
        "openai_api_key",
        "contact_proxy_secret",
        "backend_proxy_secret",
        mode="before",
    )
    @classmethod
    def empty_secret_is_unconfigured(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
