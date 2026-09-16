"""Configure hosted Supabase Auth to deliver transactional email through Resend."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SUPABASE_AUTH_CONFIG_URL = (
    "https://api.supabase.com/v1/projects/{project_ref}/config/auth"
)
EXPECTED_SMTP_CONFIG: dict[str, object] = {
    "external_email_enabled": True,
    "mailer_autoconfirm": False,
    "mailer_secure_email_change_enabled": True,
    "smtp_host": "smtp.resend.com",
    "smtp_port": 465,
    "smtp_user": "resend",
}


def _dotenv_value(path: Path, name: str) -> str | None:
    """Read one dotenv value without evaluating the file as shell code."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None

    prefix = f"{name}="
    for line in lines:
        if not line.startswith(prefix):
            continue
        value = line[len(prefix) :].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        return value or None
    return None


def _setting(name: str, *dotenv_paths: Path) -> str | None:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    for path in dotenv_paths:
        value = _dotenv_value(path, name)
        if value:
            return value
    return None


def _project_ref() -> str:
    root_env = REPOSITORY_ROOT / ".env"
    frontend_env = REPOSITORY_ROOT / "frontend" / ".env.local"
    explicit_ref = _setting("SUPABASE_PROJECT_REF", root_env, frontend_env)
    if explicit_ref:
        return explicit_ref

    supabase_url = _setting(
        "NEXT_PUBLIC_SUPABASE_URL",
        frontend_env,
        root_env,
    ) or _setting("SUPABASE_URL", root_env)
    if supabase_url:
        host = urlparse(supabase_url).hostname
        if host and host.endswith(".supabase.co"):
            return host[: -len(".supabase.co")]

    raise ValueError(
        "Set SUPABASE_PROJECT_REF, or configure a Supabase URL in .env or "
        "frontend/.env.local."
    )


def _api_request(
    *,
    method: str,
    project_ref: str,
    access_token: str,
    payload: dict[str, object] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        SUPABASE_AUTH_CONFIG_URL.format(project_ref=project_ref),
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            parsed = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"Supabase Management API returned HTTP {error.code}."
        ) from None
    except URLError as error:
        raise RuntimeError("Could not reach the Supabase Management API.") from error

    if not isinstance(parsed, dict):
        raise TypeError("Supabase Management API returned an unexpected response.")
    return parsed


def _display_config(config: dict[str, Any]) -> None:
    enabled = all(
        config.get(key) == value for key, value in EXPECTED_SMTP_CONFIG.items()
    )
    print(f"Resend SMTP configured: {'yes' if enabled else 'no'}")
    print(f"Sender: {config.get('smtp_sender_name') or 'not set'}")
    print(f"From address: {config.get('smtp_admin_email') or 'not set'}")
    print(f"SMTP host: {config.get('smtp_host') or 'not set'}")
    print(f"SMTP port: {config.get('smtp_port') or 'not set'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Show the current non-secret SMTP configuration without changing it.",
    )
    args = parser.parse_args()

    root_env = REPOSITORY_ROOT / ".env"
    access_token = _setting("SUPABASE_ACCESS_TOKEN", root_env)
    if not access_token:
        parser.error("Set SUPABASE_ACCESS_TOKEN in the environment or root .env file.")

    try:
        project_ref = _project_ref()
        if args.check:
            config = _api_request(
                method="GET",
                project_ref=project_ref,
                access_token=access_token,
            )
            _display_config(config)
            return 0

        resend_api_key = _setting("RESEND_API_KEY", root_env)
        if not resend_api_key or not resend_api_key.startswith("re_"):
            parser.error(
                "Set a valid RESEND_API_KEY in the environment or root .env file."
            )

        sender_email = _setting("RESEND_AUTH_FROM_EMAIL", root_env) or (
            "no-reply@auth.acquora.fr"
        )
        sender_name = _setting("RESEND_AUTH_SENDER_NAME", root_env) or "Acquora"
        payload = {
            **EXPECTED_SMTP_CONFIG,
            "smtp_admin_email": sender_email,
            "smtp_pass": resend_api_key,
            "smtp_sender_name": sender_name,
        }
        _api_request(
            method="PATCH",
            project_ref=project_ref,
            access_token=access_token,
            payload=payload,
        )
        config = _api_request(
            method="GET",
            project_ref=project_ref,
            access_token=access_token,
        )
        _display_config(config)

        expected = {**EXPECTED_SMTP_CONFIG, "smtp_admin_email": sender_email}
        if not all(config.get(key) == value for key, value in expected.items()):
            raise RuntimeError(
                "Supabase did not retain the expected SMTP configuration."
            )
        print("Supabase Auth will now send transactional messages through Resend.")
        return 0
    except (RuntimeError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
