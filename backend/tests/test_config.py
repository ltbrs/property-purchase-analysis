from app.core.config import Settings


def test_plain_postgresql_url_uses_installed_psycopg_driver() -> None:
    settings = Settings(database_url="postgresql://user:password@database/property")

    assert settings.database_url == ("postgresql+psycopg://user:password@database/property")
