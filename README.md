# Property Purchase Analysis

Production-oriented monorepo skeleton for a SaaS that helps home buyers in France identify document-backed property risks before purchasing. The product is decision support, not legal, notarial, engineering, energy-audit, or financial advice.

This initial setup contains a minimal Next.js application, a typed FastAPI API, and local PostgreSQL infrastructure. Product document processing and risk rules are intentionally not implemented yet.

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
| `FRONTEND_ORIGIN` | Reserved frontend origin for later CORS configuration |
| `NEXT_PUBLIC_API_URL` | API base URL exposed to the frontend |
| `DATABASE_URL` | PostgreSQL connection URL |
| `POSTGRES_DB` | Local Compose database name |
| `POSTGRES_USER` | Local Compose database user |
| `POSTGRES_PASSWORD` | Local Compose database password |
| `OBJECT_STORAGE_ENDPOINT` | S3-compatible private storage endpoint |
| `OBJECT_STORAGE_BUCKET` | Private document bucket |
| `OBJECT_STORAGE_ACCESS_KEY` | Object-storage access key |
| `OBJECT_STORAGE_SECRET_KEY` | Object-storage secret key |
| `LLM_API_KEY` | API key for the hosted LLM provider selected later |

Empty service credentials are valid for the current health-only scaffold. Never commit a populated `.env` file.

## Start local services

Start PostgreSQL on port `5432`:

```bash
docker compose up -d postgres
```

Start the backend on <http://localhost:8000>:

```bash
cd backend
uv sync
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

Database access, object-storage clients, Xberg integration, LLM-provider integration, background processing, authentication, and business rules will be added when their product behavior is implemented. This keeps the initial dependency set and architecture small.

