# Stripe production payments

Switching accounts or environments in the Stripe Dashboard does not change the
application configuration. Live and sandbox accounts have separate API keys,
products, prices, and webhook endpoints.

Acquora uses Stripe-hosted Checkout. Only `acquora-api` needs Stripe credentials.
The frontend needs no Stripe secret or publishable key for this integration.

## Configure the live account

1. Activate payments on the Acquora live account in Stripe.
2. Put a live API key in the ignored root `.env` as `STRIPE_LIVE_SECRET_KEY`.
   Keep the existing `STRIPE_SECRET_KEY`, prices, and listener secret for local
   sandbox use. Prefer a restricted live key. The setup command needs access to
   read the account, read/create Prices and Products, and read/create Webhook
   Endpoints. The application needs permission to create Checkout Sessions.
   Keep the production key in Vercel's sensitive environment variables.
3. Inspect the account and planned resources from `backend/`:

   ```bash
   uv run python -m scripts.configure_stripe_production
   ```

   Verify that the printed account ID is the intended live account.
4. Apply the configuration:

   ```bash
   uv run python -m scripts.configure_stripe_production --apply
   ```

   The command creates missing one-time EUR prices using lookup keys
   `acquora_single_analysis` (€19) and `acquora_search_pack` (€39), validates
   existing prices, and configures an endpoint at
   `https://acquora-api-acquora.vercel.app/api/v1/billing/stripe/webhook` for:

   - `checkout.session.completed`
   - `checkout.session.async_payment_succeeded`

   It writes `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
   `STRIPE_SINGLE_ANALYSIS_PRICE_ID`, and `STRIPE_SEARCH_PACK_PRICE_ID` to
   `acquora-api` in Vercel **Production only**. It never prints secret values.
   If the endpoint already exists, supply its signing secret through
   `STRIPE_LIVE_WEBHOOK_SECRET` in the ignored root `.env` before applying.
   Find that secret in Stripe Workbench under the endpoint's signing secret.
   A local `stripe listen` secret is different and cannot be used here.
5. Verify `APP_ENV=production` and `FRONTEND_ORIGIN=https://acquora.fr` on the
   backend, then redeploy the production backend to activate the variables.
   Environment updates do not change an already deployed function.

The application refuses test API keys when `APP_ENV=production` and live keys
with any other `APP_ENV` value. Keep live keys scoped to Vercel Production.
Signed webhook events must match the configured key's
mode. Managed Payments and Adaptive Pricing are disabled per Checkout Session so
Acquora remains the merchant and fulfillment receives the expected EUR amount.
The setup does not enable automatic tax collection; the price's inclusive
tax behavior alone does not calculate tax or establish a tax registration.

## Test the complete payment flow in the sandbox

Keep local development pointed at the existing Stripe test account and a local
database. Start the backend and frontend, then run from `backend/`:

```bash
uv run python -m scripts.stripe_listen
```

Sign in at `http://localhost:3000`, open `/app/compte`, and buy each offer.
Use a future expiry date and any three-digit CVC with these Stripe test cards:

| Scenario | Card | Expected result |
| --- | --- | --- |
| Success | `4242 4242 4242 4242` | One credit for €19, three for €39 |
| Authentication required | `4000 0000 0000 3220` | Complete authentication, then receive credits |
| Declined | `4000 0000 0000 0002` | No credits |
| Cancel Checkout | No card required | Return to the account, no credits |

Also check that activating one dossier consumes one credit and activating that
same dossier again consumes none. The automated billing tests below verify that
duplicate webhook deliveries do not increase the balance again. If you also have
a public sandbox webhook endpoint, resend the successful Checkout event to that
endpoint in Workbench and verify the same behavior. Closing the return page after
payment must still grant
credits because fulfillment is driven by the webhook.

Use Checkout initiated from Acquora for end-to-end tests. Generic
`stripe trigger checkout.session.completed` events have no corresponding Acquora
purchase and are rejected. For repeat webhook tests with the CLI, use
`stripe events resend EVENT_ID --webhook-endpoint ENDPOINT_ID` for a configured
sandbox endpoint. For a local listener, use the automated billing tests below
to verify duplicate delivery handling.

```bash
uv run pytest tests/test_billing.py tests/test_stripe_gateway.py
```

## Check production without a charge

Sign in at `https://acquora.fr/app/compte`, open Checkout for both offers, and
verify the merchant, €19/€39 prices, EUR currency, and absence of the test-mode
banner. Cancel and check the return URL and unchanged credit balance.

In Stripe Workbench, confirm that the live webhook destination is enabled,
subscribes to both events, and has no failed deliveries. After a genuine customer
purchase, verify a `2xx` delivery, the correct credit balance, and a single grant
when that event is resent. Opening and cancelling Checkout does not validate
paid fulfillment; that is covered by sandbox tests until a genuine purchase.

Test cards only work in a sandbox. Stripe prohibits testing live payments with
real payment methods. Do not make a live purchase and refund it solely as a test.
See [Stripe's testing guide](https://docs.stripe.com/testing) and
[go-live checklist](https://docs.stripe.com/get-started/checklist/go-live).
