import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def isolate_auth_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep test authentication independent from the developer's local .env."""
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "backend_proxy_secret", None)
    monkeypatch.setattr(settings, "supabase_url", None)
