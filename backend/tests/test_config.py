from app.core.config import Settings
from pydantic import ValidationError
import pytest


def test_plain_postgresql_url_uses_installed_psycopg_driver() -> None:
    settings = Settings(database_url="postgresql://user:password@database/property")

    assert settings.database_url == ("postgresql+psycopg://user:password@database/property")


def test_document_view_url_ttl_is_bounded() -> None:
    assert Settings().document_view_url_ttl_seconds == 300
    with pytest.raises(ValidationError):
        Settings(document_view_url_ttl_seconds=59)
    with pytest.raises(ValidationError):
        Settings(document_view_url_ttl_seconds=3601)
