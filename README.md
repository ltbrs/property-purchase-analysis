# Property Purchase Analysis

Production-oriented monorepo skeleton for a SaaS that helps home buyers in France identify document-backed property risks before purchasing. The product is decision support, not legal, notarial, engineering, energy-audit, or financial advice.

The current implementation contains a Next.js upload flow, a typed FastAPI API,
PostgreSQL persistence, private S3-compatible PDF storage, and page-level PDF
extraction through Xberg. Classification, structured fact extraction, and risk
rules are intentionally not implemented yet.

## Repository layout

```text
frontend/             Next.js App Router application
  app/                Landing, upload, and analysis routes
  components/         Shared application shell
  features/           Future feature modules
  lib/                Shared frontend utilities
backend/              FastAPI application managed with uv
  app/api/            HTTP routes
  app/core/           Settings and cross-cutting configuration
  app/documents/      Parser, classification, and extraction boundaries
  app/property/       Normalized property model boundaries
  app/risks/          Deterministic risk model, rules, and engine boundaries
  app/reports/        Report assembly boundary
  app/llm/            Hosted LLM adapter boundary
  app/storage/        Private object-storage boundary
  app/jobs/           Explicit processing workflow boundary
  tests/              Backend tests
```

## Prerequisites

- Node.js 20.9 or newer and npm
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Docker with Compose, only if running PostgreSQL locally

## Environment

Copy the example configuration before local development:

```bash
cp .env.example .env
```

The initial scaffold recognizes these variables:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Backend runtime environment (`development` by default) |
| `FRONTEND_ORIGIN` | Allowed browser origin for the API |
| `NEXT_PUBLIC_API_URL` | API base URL exposed to the frontend |
| `DATABASE_URL` | PostgreSQL connection URL |
| `POSTGRES_DB` | Local Compose database name |
| `POSTGRES_USER` | Local Compose database user |
| `POSTGRES_PASSWORD` | Local Compose database password |
| `OBJECT_STORAGE_ENDPOINT` | S3-compatible private storage endpoint |
| `OBJECT_STORAGE_BUCKET` | Private document bucket |
| `OBJECT_STORAGE_REGION` | S3 signing region (`eu-west-3` by default) |
| `OBJECT_STORAGE_ACCESS_KEY` | Object-storage access key |
| `OBJECT_STORAGE_SECRET_KEY` | Object-storage secret key |
| `MAX_UPLOAD_SIZE_BYTES` | Maximum PDF size (25 MiB by default) |
| `LLM_API_KEY` | API key for the hosted LLM provider selected later |

Never commit a populated `.env` file. Replace the example object-storage secret
outside local development.

## Start local services

Start PostgreSQL and the private MinIO-compatible object store:

```bash
docker compose up -d postgres object-storage object-storage-init
```

The storage API listens on port `9000`; its local administration console listens
on port `9001`. The init container creates the configured bucket and explicitly
keeps anonymous access disabled.

Apply the database migration, then start the backend on
<http://localhost:8000>:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

The health endpoint is available at <http://localhost:8000/api/v1/health> and interactive API documentation at <http://localhost:8000/docs>.

In another terminal, start the frontend on <http://localhost:3000>:

```bash
cd frontend
npm install
npm run dev
```

## Quality checks

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Backend:

```bash
cd backend
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
```

## Document upload API

The upload slice provides these case-scoped endpoints:

```text
POST /api/v1/analysis-cases
GET  /api/v1/analysis-cases/{case_id}/documents
POST /api/v1/analysis-cases/{case_id}/documents
POST /api/v1/analysis-cases/{case_id}/documents/{document_id}/extract
```

Only PDFs are accepted. The API validates the declared MIME type, checks for a PDF
signature, enforces the configured size limit, stores the bytes outside PostgreSQL,
and persists only metadata and processing state. Re-uploading identical bytes to
the same case returns the existing document.

Extraction is an explicit authenticated operation. It retrieves the PDF from
private storage, runs Xberg behind the internal `PdfParser` interface, and persists
one ordered record per page. Each page retains its one-based page number, text, and
structured tables; document metadata, parser name/version, and extraction duration
are stored on the parent extraction record. A successful retry returns the existing
extraction rather than parsing the document again. Parser failures set the document
to `failed` without saving partial page output and can be retried.

Ownership is checked in every case-scoped database query. For this pre-login MVP,
`X-User-Id` represents an identity asserted by the authentication boundary; the
frontend creates a local development identity. A production edge must authenticate
the user, replace this header, and prevent clients from overriding it.

## Architecture direction

The future document workflow will stay explicit:

```text
PDF upload
-> file validation
-> PDF extraction (Xberg by default)
-> document classification
-> structured extraction
-> normalized property model
-> deterministic risk rules
-> cross-document checks
-> LLM explanation
-> source-backed report
```

LLM-provider integration, background processing, production authentication, and
business rules remain deferred. Upload still stops at `uploaded`; callers explicitly
start extraction through the extraction endpoint so the workflow remains visible.

## Known PDF extraction limitations

- Extraction currently runs synchronously in the API request. Moving it to a durable
  worker is deferred until processing volume justifies job infrastructure.
- No second parser or vision fallback is configured. Scanned or image-only pages may
  therefore produce little or no text depending on Xberg's available local OCR support.
- Password-protected PDFs are not supplied with passwords and will fail cleanly.
- Complex or borderless tables are heuristic and may be incomplete or represented as
  ordinary page text. The stored output preserves what Xberg reports without inventing
  missing cells.
- Only common document metadata is normalized. Parser-specific metadata is retained
  only when Xberg exposes it through its additional metadata map.
