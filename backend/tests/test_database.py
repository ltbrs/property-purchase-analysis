from unittest.mock import patch

from app.core.config import Settings
from app.core.database import get_engine


def test_transaction_pooler_disables_prepared_statements() -> None:
    settings = Settings(
        database_url="postgresql://user:password@pooler.supabase.com:6543/postgres"
    )

    get_engine.cache_clear()
    with (
        patch("app.core.database.get_settings", return_value=settings),
        patch("app.core.database.create_engine") as create_engine,
    ):
        get_engine()

    create_engine.assert_called_once_with(
        "postgresql+psycopg://user:password@pooler.supabase.com:6543/postgres",
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"prepare_threshold": None},
    )
    get_engine.cache_clear()


def test_session_pooler_keeps_prepared_statements_enabled() -> None:
    settings = Settings(
        database_url="postgresql://user:password@pooler.supabase.com:5432/postgres"
    )

    get_engine.cache_clear()
    with (
        patch("app.core.database.get_settings", return_value=settings),
        patch("app.core.database.create_engine") as create_engine,
    ):
        get_engine()

    create_engine.assert_called_once_with(
        "postgresql+psycopg://user:password@pooler.supabase.com:5432/postgres",
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={},
    )
    get_engine.cache_clear()
