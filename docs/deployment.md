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
 api.acquora.fr, FastAPI on a persistent container host
            |
            +--> Supabase Postgres
            +--> private Supabase Storage through its S3 endpoint
```

OVH remains the registrar and authoritative DNS provider. Vercel serves the
frontend. The FastAPI service should use a persistent container host because
document uploads can reach 25 MiB and PDF extraction is synchronous. An OVH VPS
is suitable, but the repository does not assume that an OVH DNS subscription
also includes a server.

## Current Vercel setup

The Vercel team contains a project named `acquora`. Its Git root directory is
`frontend`, its Node.js runtime is 22.x, and the `acquora-prod` Supabase resource
is connected for Production, Preview, and Development.

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
other unrelated records when changing the web records. Add an `A` or `AAAA`
record for `api.acquora.fr` only after the backend host has a stable public IP.

## Vercel environment

The Supabase Marketplace integration manages its own variables. The application
does not expose Supabase service credentials to browser code and does not need
the managed Supabase variables in the frontend today.

Add these application variables in Vercel for Production and Preview:

| Variable | Value or source |
| --- | --- |
| `AUTH_URL` | `https://acquora.fr` in Production |
| `AUTH_SECRET` | A random value generated with `openssl rand -hex 32` |
| `AUTH_GOOGLE_ID` | Google OAuth web client ID |
| `AUTH_GOOGLE_SECRET` | Google OAuth client secret |
| `BACKEND_API_URL` | `https://api.acquora.fr/api/v1` |
| `BACKEND_PROXY_SECRET` | A dedicated random value, identical on FastAPI |
| `CONTACT_PROXY_SECRET` | A second random value, identical on FastAPI |

Never prefix the proxy secrets, Google client secret, or Auth.js secret with
`NEXT_PUBLIC_`. Add these Google OAuth redirect URIs:

```text
https://acquora.fr/api/auth/callback/google
https://www.acquora.fr/api/auth/callback/google
```

## Supabase database

For a persistent FastAPI container, use the Supabase session pooler URL on port
5432 when the host needs IPv4. The Vercel integration exposes this as
`POSTGRES_URL_NON_POOLING`. Copy its value to the backend as `DATABASE_URL`.
The application also recognizes `POSTGRES_URL_NON_POOLING` and `POSTGRES_URL` as
fallback names. `DATABASE_URL` has priority when more than one is present.

The URL must require TLS. Keep the Supabase supplied `sslmode=require` query
parameter. Apply migrations from the backend release image before restarting
the service:

```bash
alembic upgrade head
```

## Supabase private storage

In Supabase Storage:

1. Create a bucket named `property-documents` and keep it private.
2. Enable the S3 protocol.
3. Generate server-side S3 access keys in Storage settings.
4. Copy the direct storage endpoint and region shown by Supabase.

Configure the FastAPI container with:

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

The production container needs the following values in its private environment:

```dotenv
APP_ENV=production
FRONTEND_ORIGIN=https://acquora.fr
DATABASE_URL=SUPABASE_SESSION_POOLER_URL
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

Do not switch production traffic to Vercel until this is resolved. The intended
solution is a two-step upload:

1. The authenticated Next.js boundary requests a short-lived, case-scoped
   upload URL from FastAPI.
2. The browser uploads directly to private Supabase Storage, then FastAPI
   downloads and validates the PDF signature, size, and checksum before it
   persists document metadata.

The signed URL must authorize one generated object key only. The browser must
never receive the Supabase S3 access key, secret key, service-role key, or the
backend proxy secret.

Build and check the production image from the repository root with:

```bash
docker build -t acquora-backend:local backend
docker run --rm --env-file .env -p 8000:8000 acquora-backend:local
```

Terminate TLS in front of the container, expose only ports 80 and 443 publicly,
and do not expose Postgres or the container's port 8000 directly.

## GitHub and releases

The `Test` workflow runs frontend and backend checks for pull requests targeting
`main` and again after a commit lands on `main`. It needs no repository secrets.

Vercel Git deployments require a GitHub login connection on the Vercel account.
After adding it, connect `ltbrs/property-purchase-analysis` to the `acquora`
project. The Production Branch must be `main`, and the Root Directory must remain
`frontend`. Vercel then creates Preview deployments for other branches and a
Production deployment for `main` without GitHub Actions credentials.

Backend continuous deployment depends on the selected persistent host. Do not
add SSH secrets or a release workflow until the OVH VPS or alternative host is
confirmed. At minimum, that workflow will need the host, user, SSH private key,
known-host fingerprint, and deployment directory. Keep the production `.env` on
the server, not in GitHub.
