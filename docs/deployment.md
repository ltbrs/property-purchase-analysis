# Production deployment

The intended MVP topology is:

```text
acquora.fr and www.acquora.fr
            |
            v
       Vercel Next.js
            |
            | server-only requests with shared boundary secrets
            v
       Vercel FastAPI
            |
            +--> Supabase Postgres
            +--> private Supabase Storage through its S3 endpoint
```

OVH remains the registrar and authoritative DNS provider. It does not provide
application compute with the current domain-only subscription. Vercel serves
both applications as separate projects. FastAPI runs as one Python Function in
Paris, close to the Supabase project.

## Current Vercel setup

The Vercel team contains two projects connected to the same GitHub repository:

| Project | Git root | Runtime | Data integration |
| --- | --- | --- | --- |
| `acquora` | `frontend` | Next.js, Node.js 22 | Supabase Auth only |
| `acquora-api` | `backend` | FastAPI, Python 3.12, Fluid compute in `cdg1` | `acquora-prod` |

Both projects use `main` as the Production Branch. Other branches produce
Preview deployments. The frontend uses the Supabase project only for Auth.
Application data continues to travel through FastAPI and is never queried
through the browser Data API.

Keep Vercel Authentication enabled for preview deployments only on
`acquora-api`. Its production URL must be reachable by the frontend's
server-side proxy. FastAPI separately requires `BACKEND_PROXY_SECRET` and an
authenticated user identity on every analysis route, while the health route is
intentionally public. Enabling Vercel Authentication on production API URLs
causes the proxy to receive Vercel's HTML login page instead of JSON.

The domains `acquora.fr` and `www.acquora.fr` are assigned to the project. At
OVH, replace the current parking records with the exact records displayed by
Vercel. At the time this setup was created, Vercel requested:

```text
A  @    76.76.21.21
A  www  76.76.21.21
```

The application permanently redirects `www.acquora.fr` to the canonical apex
domain while preserving the path and query string.

Inspect the domains again before changing DNS because Vercel can provide
project-specific values:

```bash
cd frontend
vercel domains inspect acquora.fr --scope acquora
vercel domains inspect www.acquora.fr --scope acquora
```

Keep OVH nameservers if OVH continues to manage DNS. Do not remove MX, TXT, or
other unrelated records when changing the web records.

After the first successful `main` deployment of `acquora-api`, assign its API
subdomain and inspect the exact DNS requirement:

```bash
vercel domains add api.acquora.fr acquora-api --scope acquora
vercel domains inspect api.acquora.fr --scope acquora
```

Add the displayed `api` record in the OVH DNS zone. Do not guess the target.
Once Vercel verifies it, change `BACKEND_API_URL` on the frontend project to
`https://api.acquora.fr/api/v1`.

## Vercel environment

The Supabase Marketplace integration manages database variables on
`acquora-api`. The frontend only receives the values it needs for its server-side
proxy. No Supabase service credential is exposed to browser code.

Add these application variables in Vercel for Production and Preview:

| Variable | Value or source |
| --- | --- |
| `NEXT_PUBLIC_SITE_URL` | `https://acquora.fr` in Production |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Browser-safe Supabase publishable key |
| `AUTH_GOOGLE_ID` | Google OAuth web client ID, also configured in the Supabase Google provider |
| `BACKEND_API_URL` | `https://acquora-api-acquora.vercel.app/api/v1`, then `https://api.acquora.fr/api/v1` after DNS validation |
| `BACKEND_PROXY_SECRET` | A dedicated random value, identical on FastAPI |
| `CONTACT_PROXY_SECRET` | A second random value, identical on FastAPI |
| `NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN` | Public PostHog project token |
| `NEXT_PUBLIC_POSTHOG_HOST` | PostHog ingestion host, such as `https://eu.i.posthog.com` |

Never prefix the proxy secrets, Google client secret, SMTP secret, or a Supabase
secret key with `NEXT_PUBLIC_`. `AUTH_GOOGLE_ID` is a public client identifier,
but it is passed from the server to the sign-in component instead of being a
global public environment variable.

Add `https://acquora.fr` as an authorized JavaScript origin on the Google OAuth
web client. Add `http://localhost:3000` for local development. Register that web
client ID in the Supabase Google provider. Acquora does not use the Supabase
OAuth redirect URL for Google sign-in.

Set the Supabase Auth Site URL to `https://acquora.fr`. Allow
`https://acquora.fr/auth/callback` and `http://localhost:3000/**`. The local
wildcard is required because Auth callback URLs include a `next` query parameter.
Add any required preview callbacks separately.
Enable confirmed e-mail addresses, custom SMTP, security notifications, bot
protection, and an asymmetric ES256 signing key. Google Identity Services returns
an ID token directly to Acquora. The frontend passes that token and a verified
nonce to Supabase Auth, which creates the cookie-backed session through
`@supabase/ssr`. Callback routes remain in use for email confirmation and
password recovery.

## Supabase Auth email through Resend

Resend is only the delivery provider for Supabase Auth transactional messages:
account confirmation, password recovery, email changes, invitations, and account
security notifications. Supabase continues to create the links and email content.
Do not add the Resend SDK or a custom email endpoint for this flow.

Use the dedicated sending domain `auth.acquora.fr` and the sender
`Acquora <no-reply@auth.acquora.fr>`. This isolates authentication delivery from
future application or marketing mail. The address does not need a mailbox, but the
domain must be verified in Resend before public delivery works.

1. Create the Resend account and add `auth.acquora.fr` under Domains.
2. Copy the exact SPF, DKIM, and MX records generated by Resend into the OVH DNS
   zone. Do not alter existing website or inbound-mail records. Wait until Resend
   marks the domain as verified.
3. Create a Resend API key named `Acquora Supabase Auth production`, with Sending
   access restricted to `auth.acquora.fr`.
4. Put the key temporarily in the ignored root `.env` file:

   ```dotenv
   RESEND_API_KEY=re_REPLACE_ME
   ```

   `SUPABASE_ACCESS_TOKEN` must also be present. The configuration script derives
   the project reference from `frontend/.env.local`. `SUPABASE_PROJECT_REF` can be
   set explicitly if that URL is unavailable.
5. Apply and then inspect the hosted Auth configuration:

   ```bash
   python3 scripts/configure_supabase_auth_smtp.py
   python3 scripts/configure_supabase_auth_smtp.py --check
   ```

The command configures these Supabase values without printing either secret:

| Supabase setting | Value |
| --- | --- |
| Sender name | `Acquora` |
| Sender email | `no-reply@auth.acquora.fr` |
| SMTP host | `smtp.resend.com` |
| SMTP port | `465` |
| SMTP username | `resend` |
| SMTP password | Resend API key |

The Resend key is stored by hosted Supabase, so it is not a frontend, FastAPI, or
Vercel runtime variable for Auth. Keep the recoverable copy in a password manager
and remove it from the local `.env` after the setup succeeds. For future Stripe
transactional messages, reuse the Resend account and verified-domain strategy, but
create a separate sending key so each integration can be rotated independently.

After configuration, test both signup confirmation and password recovery with an
address that is not a member of the Supabase organization. Confirm the messages in
the Resend delivery logs and verify that their links return to `https://acquora.fr`.
Hosted Supabase starts custom SMTP at 30 messages per hour. Resend plan limits also
apply independently.

## Product and web analytics

PostHog is the product analytics boundary. Its browser setup lives in
`frontend/lib/analytics/product-analytics.ts` and is initialized by
`frontend/instrumentation-client.ts`. It records page views, referrers, campaign
parameters, browser and device properties, and the explicit product events defined
in the application. Authenticated users are linked with the stable application user
ID and an `auth_provider` property. Autocapture and exception capture stay disabled.
Session recording starts only after an authenticated user is identified and stops on
logout or when the authenticated application shell unmounts. Product text and input
values are masked, document frames and file inputs are blocked, and replay network
payloads, URLs, headers, console logs, cross-origin frames, and canvases are not
captured. Sampling and recording triggers remain controlled by the PostHog project.

Vercel Web Analytics is the independent, cookie-free traffic analytics boundary.
Enable it in the Vercel project dashboard, then keep
`frontend/components/analytics/vercel-web-analytics.tsx` mounted from the root
layout. It provides global page, referrer, geography, browser, operating-system, and
device reporting without receiving PostHog product events.

## Supabase database

Vercel automatically supplies `POSTGRES_URL` to `acquora-api`. It is the
transaction-pooler URL on port 6543 and is the correct default for serverless
functions. The application disables named prepared statements for that mode,
accepts Vercel's `postgres://` scheme, and removes the integration-only `supa`
query parameter before passing the URL to psycopg.

An explicit `DATABASE_URL` remains the highest-priority override for local or
future persistent hosts. `POSTGRES_URL_NON_POOLING` is the final fallback.

The URL must require TLS. Keep the Supabase supplied `sslmode=require` query
parameter. Apply migrations before deploying application code that depends on
them:

```bash
alembic upgrade head
```

## Supabase private storage

In Supabase Storage:

1. Create a bucket named `property-documents` and keep it private.
2. Enable the S3 protocol.
3. Generate server-side S3 access keys in Storage settings.
4. Copy the direct storage endpoint and region shown by Supabase.

Configure the FastAPI project with:

```dotenv
OBJECT_STORAGE_ENDPOINT=https://PROJECT_REF.storage.supabase.co/storage/v1/s3
OBJECT_STORAGE_BUCKET=property-documents
OBJECT_STORAGE_REGION=PROJECT_REGION
OBJECT_STORAGE_ACCESS_KEY=SERVER_SIDE_S3_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY=SERVER_SIDE_S3_SECRET_KEY
DOCUMENT_UPLOAD_URL_TTL_SECONDS=300
```

These S3 keys bypass Storage RLS and can access every bucket in the project.
Keep them only on the backend. Supabase Storage deletion is permanent, so the
application's document deletion behavior must be treated accordingly.

The browser uploads PDFs directly with a short-lived, server-generated S3 URL.
The S3 endpoint must therefore be reachable from the browser and allow `PUT`
requests from the frontend origin. Set `OBJECT_STORAGE_PUBLIC_ENDPOINT` only
when the backend's `OBJECT_STORAGE_ENDPOINT` uses a private hostname.

## FastAPI environment

The `acquora-api` project needs the following application values in its private
environment. `POSTGRES_URL` and related database values come from the connected
Supabase resource and should not be copied manually.

```dotenv
APP_ENV=production
FRONTEND_ORIGIN=https://acquora.fr
OBJECT_STORAGE_ENDPOINT=https://PROJECT_REF.storage.supabase.co/storage/v1/s3
OBJECT_STORAGE_BUCKET=property-documents
OBJECT_STORAGE_REGION=PROJECT_REGION
OBJECT_STORAGE_ACCESS_KEY=SERVER_SIDE_S3_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY=SERVER_SIDE_S3_SECRET_KEY
DOCUMENT_UPLOAD_URL_TTL_SECONDS=300
OPENAI_API_KEY=SERVER_SIDE_OPENAI_KEY
STRIPE_SECRET_KEY=sk_live_SERVER_SIDE_STRIPE_KEY
STRIPE_WEBHOOK_SECRET=whsec_STRIPE_ENDPOINT_SECRET
STRIPE_SINGLE_ANALYSIS_PRICE_ID=price_SINGLE_ANALYSIS
STRIPE_SEARCH_PACK_PRICE_ID=price_SEARCH_PACK
BACKEND_PROXY_SECRET=SAME_VALUE_AS_VERCEL
CONTACT_PROXY_SECRET=SAME_VALUE_AS_VERCEL
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated
```

The backend rejects authenticated requests when the backend boundary secret is
or Supabase configuration is missing in production. Every analysis request
requires both the private proxy secret and a Supabase access token verified
through the project JWKS endpoint. The contact endpoint independently requires
its contact proxy secret. The health endpoint and the signed Stripe webhook
endpoint are the only intentionally public routes. Stripe verifies the raw
webhook body before any purchase or credit is changed.

### Large upload boundary

The current browser upload travels through the Next.js `/api/backend` route.
Vercel Functions limit request and response bodies to 4.5 MB, while Acquora
accepts PDFs up to 25 MiB. Files above the Vercel limit will therefore fail
before they reach FastAPI.

The application can run on Vercel, but files above this limit cannot use the
current proxied upload route. The intended solution is a two-step upload:

1. The authenticated Next.js boundary requests a short-lived, case-scoped
   upload URL from FastAPI.
2. The browser uploads directly to private Supabase Storage, then FastAPI
   downloads and validates the PDF signature, size, and checksum before it
   persists document metadata.

The signed URL must authorize one generated object key only. The browser must
never receive the Supabase S3 access key, secret key, service-role key, or the
backend proxy secret.

The Docker image remains available if document processing later moves to a
persistent worker or container host:

```bash
docker build -t acquora-backend:local backend
docker run --rm --env-file .env -p 8000:8000 acquora-backend:local
```

## GitHub and releases

The `Test` workflow runs frontend and backend checks for pull requests targeting
`main` and again after a commit lands on `main`. It needs no repository secrets.

Vercel Git deployments are connected for both `acquora` and `acquora-api`.
Vercel creates Preview deployments for other branches and Production deployments
for `main`. No Vercel token or deployment secret is needed in GitHub Actions.

The GitHub `Test` workflow also needs no secrets. The frontend also needs the
Supabase project URL and publishable key. Google and SMTP secrets are configured
in Supabase Auth rather than in the Vercel frontend.
