"""Forward local test payments using the Stripe account configured in .env."""

import os
import re
import shutil
import subprocess

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    key = settings.stripe_secret_key
    if settings.app_env != "development" or key is None:
        raise SystemExit("Configure APP_ENV=development and STRIPE_SECRET_KEY in the root .env.")
    if not key.get_secret_value().startswith(("sk_test_", "rk_test_")):
        raise SystemExit("Local webhook forwarding requires a Stripe test key.")
    executable = shutil.which("stripe")
    if executable is None:
        raise SystemExit("Install the Stripe CLI before starting local webhook forwarding.")

    environment = {**os.environ, "STRIPE_API_KEY": key.get_secret_value()}
    result = subprocess.run(
        [executable, "listen", "--print-secret", "--skip-update"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    secret = result.stdout.strip()
    if result.returncode != 0 or not secret.startswith("whsec_"):
        raise SystemExit("Stripe could not prepare the listener. Check your test API key.")
    configured = settings.stripe_webhook_secret
    if configured is None or configured.get_secret_value() != secret:
        raise SystemExit(
            "STRIPE_WEBHOOK_SECRET does not match this listener. Run stripe listen with the same "
            "test account, copy its signing secret into the root .env, and restart the backend."
        )

    print("Forwarding Stripe test payments to http://localhost:8000/api/v1/billing/stripe/webhook")
    with subprocess.Popen(
        [
            executable,
            "listen",
            "--skip-update",
            "--events",
            "checkout.session.completed,checkout.session.async_payment_succeeded",
            "--forward-to",
            "localhost:8000/api/v1/billing/stripe/webhook",
        ],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as listener:
        try:
            assert listener.stdout is not None
            for line in listener.stdout:
                print(re.sub(r"whsec_\S+", "[signing secret hidden]", line), end="", flush=True)
        except KeyboardInterrupt:
            listener.terminate()
        raise SystemExit(listener.wait())


if __name__ == "__main__":
    main()
