import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_plain_postgresql_url_uses_installed_psycopg_driver() -> None:
    settings = Settings(database_url="postgresql://user:password@database/property")

    assert settings.database_url == ("postgresql+psycopg://user:password@database/property")


def test_supabase_vercel_database_variable_is_supported() -> None:
    settings = Settings.model_validate(
        {
            "POSTGRES_URL_NON_POOLING": (
                "postgresql://user:password@pooler.supabase.com:5432/postgres"
            )
        }
    )

    assert settings.database_url == (
        "postgresql+psycopg://user:password@pooler.supabase.com:5432/postgres"
    )


def test_document_view_url_ttl_is_bounded() -> None:
    assert Settings().document_view_url_ttl_seconds == 300
    with pytest.raises(ValidationError):
        Settings(document_view_url_ttl_seconds=59)
    with pytest.raises(ValidationError):
        Settings(document_view_url_ttl_seconds=3601)


def test_blank_openai_api_key_is_treated_as_unconfigured() -> None:
    assert Settings(openai_api_key="   ").openai_api_key is None


def test_blank_proxy_secrets_are_treated_as_unconfigured() -> None:
    settings = Settings(contact_proxy_secret=" ", backend_proxy_secret=" ")

    assert settings.contact_proxy_secret is None
    assert settings.backend_proxy_secret is None
