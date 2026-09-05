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
| `acquora` | `frontend` | Next.js, Node.js 22 | None |
| `acquora-api` | `backend` | FastAPI, Python 3.12, Fluid compute in `cdg1` | `acquora-prod` |

Both projects use `main` as the Production Branch. Other branches produce
Preview deployments. The Supabase integration is intentionally absent from the
frontend because it does not query Supabase directly.

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
| `AUTH_URL` | `https://acquora.fr` in Production |
| `AUTH_SECRET` | A random value generated with `openssl rand -hex 32` |
| `AUTH_GOOGLE_ID` | Google OAuth web client ID |
| `AUTH_GOOGLE_SECRET` | Google OAuth client secret |
| `BACKEND_API_URL` | `https://acquora-api-acquora.vercel.app/api/v1`, then `https://api.acquora.fr/api/v1` after DNS validation |
| `BACKEND_PROXY_SECRET` | A dedicated random value, identical on FastAPI |
| `CONTACT_PROXY_SECRET` | A second random value, identical on FastAPI |

Never prefix the proxy secrets, Google client secret, or Auth.js secret with
`NEXT_PUBLIC_`. Add these Google OAuth redirect URIs:

```text
https://acquora.fr/api/auth/callback/google
https://www.acquora.fr/api/auth/callback/google
```

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
```

These S3 keys bypass Storage RLS and can access every bucket in the project.
Keep them only on the backend. Supabase Storage deletion is permanent, so the
application's document deletion behavior must be treated accordingly.

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
OPENAI_API_KEY=SERVER_SIDE_OPENAI_KEY
BACKEND_PROXY_SECRET=SAME_VALUE_AS_VERCEL
CONTACT_PROXY_SECRET=SAME_VALUE_AS_VERCEL
```

The backend rejects authenticated requests when the backend boundary secret is
missing in production. The contact endpoint independently requires its contact
proxy secret. Only `/api/v1/health` is intentionally public.

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

The GitHub `Test` workflow also needs no secrets. The remaining credentials are
Vercel project environment variables, specifically `AUTH_SECRET`,
`AUTH_GOOGLE_ID`, and `AUTH_GOOGLE_SECRET` for the frontend authentication flow.
