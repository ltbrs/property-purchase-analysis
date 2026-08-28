# Property Purchase Analysis

Production-oriented monorepo skeleton for a SaaS that helps home buyers in France identify document-backed property risks before purchasing. The product is decision support, not legal, notarial, engineering, energy-audit, or financial advice.

The current implementation contains a Next.js upload flow, a typed FastAPI API,
PostgreSQL persistence, private S3-compatible PDF storage, page-level PDF
extraction through Xberg, document classification, source-backed structured fact
extraction, deterministic risk rules, and cross-document reconciliation.
It also detects missing or insufficient documents and generates a persisted,
buyer-facing report organized by decision priority.

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
| `DOCUMENT_VIEW_URL_TTL_SECONDS` | Lifetime of private PDF viewing links (5 minutes by default) |
| `MAX_UPLOAD_SIZE_BYTES` | Maximum PDF size (25 MiB by default) |
| `OPENAI_API_KEY` | Server-side OpenAI API key used for structured extraction |

The model is deliberately fixed to `gpt-5.6-luna` in the server-side adapter; it
cannot be selected by a request or changed through environment configuration.

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
POST /api/v1/analysis-cases/{case_id}/documents/{document_id}/classify
POST /api/v1/analysis-cases/{case_id}/documents/{document_id}/extract-dpe
POST /api/v1/analysis-cases/{case_id}/documents/{document_id}/extract-structured
POST /api/v1/analysis-cases/{case_id}/findings/refresh
GET  /api/v1/analysis-cases/{case_id}/findings
POST /api/v1/analysis-cases/{case_id}/report/refresh
GET  /api/v1/analysis-cases/{case_id}/report
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

Classification is a separate operation after PDF extraction. Its version-controlled
prompt requests one of the initial document categories, confidence, dates/covered
period, issuer, and extraction strategy. A model confidence below `0.70` is
deterministically stored as `unknown`; the original validated output and the requested
and resolved model identifiers remain persisted for audit.

DPE extraction is available only after the document is classified as `dpe`. Each
non-null normalized fact contains the source document ID, one-based page number, and
a short quote. Code verifies that the quote occurs on that page and converts invalid
ratings, numeric ranges, dates, reversed cost ranges, and unsupported citations to
explicit null values. It does not produce risks or infer absent facts. Both analysis
operations are authenticated and idempotent.

The structured extractor routes classified AG minutes, copropriété financial/charge
documents, diagnostics, and ERP statements into separate strict schemas behind one
small persistence boundary. AG items preserve meeting date, resolution, exact status,
explicit total and lot-share amounts, and source page. Financial items preserve covered
periods and due dates. Diagnostics cover asbestos, lead, electricity, gas, ERP, and
Carrez without inferring legal consequences. Unsupported classifications return a
conflict rather than being forced through the wrong schema.

Refreshing case findings runs deterministic rules only. It evaluates DPE energy and
validity facts; voted and repeatedly discussed copropriété work; recurring infiltration;
explicit lot costs, unpaid charges, and upcoming payments; diagnostic facts; and
cross-document inconsistencies. Findings distinguish `confirmed`, `likely`, `possible`,
and `missing_information`, retain every supporting source, and are replaced atomically
on refresh. The response also includes a chronological AG/financial timeline. No raw
document text or LLM judgment is used by the rule or reconciliation engines.

The same refresh now checks whether the dossier contains a usable DPE, recent AG
minutes, copropriété financial information, and supporting financial documents for
mentioned works. Every missing-document finding distinguishes an absent document from
an insufficient one and labels it as `definitely_expected`, `usually_useful`, or
`context_dependent`. These are product completeness rules, not assertions that a
document is legally mandatory.

Report refresh persists a deterministic snapshot assembled from validated facts and
findings. Sections are ordered for a buyer: financial, building/copropriété, energy,
diagnostics, inconsistencies, missing information, then explicit reassuring facts.
Every source-backed item includes the original filename and page. Reassuring items are
created only from explicit favorable DPE or diagnostic facts; the report does not infer
that silence means safety. The `/analysis` route renders this structured report without
a chatbot. Secure source-document links and in-document page inspection remain step 14.

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

Background processing and production authentication remain deferred.
Upload still stops at `uploaded`; callers explicitly advance each stage so the workflow
remains visible.

## Evaluation fixtures

Golden classification and DPE fixtures live in `backend/evals/fixtures`. They include
multiple DPE layouts, a copropriété AG example, and incomplete content. Live evaluation
is opt-in because it calls the API:

```bash
cd backend
uv run python -m evals.run_document_evals classification
uv run python -m evals.run_document_evals dpe
uv run python -m evals.run_document_evals ag_minutes
uv run python -m evals.run_document_evals financials
uv run python -m evals.run_document_evals diagnostics
```

## Deterministic rule boundaries

The initial thresholds are explicit product heuristics, not legal conclusions:

- DPE rating E/F/G maps to medium/high/critical; consumption starts at 250, 330,
  and 450 kWh/m²/year; the projected annual-cost rule starts at €2,000 and becomes
  high at €3,000.
- A DPE is expired only when its explicit validity date is before the analysis date.
  Missing rating, consumption, issue date, or validity date is surfaced separately.
- An explicit property share starts being highlighted at €5,000 and becomes high at
  €10,000. Unpaid charges start being highlighted at €5,000. Discussed work is never
  promoted to voted work.
- An annual charge increase is material at 20% or €500. Upcoming exposure uses only
  explicit amounts; the lot share is preferred and never estimated.
- Surface differences require both more than 1 m² and more than 2%. They are described
  as possible inconsistencies because DPE and Carrez measurements can use different
  perimeters.
- AG minutes are treated as recent at the inclusive three-year boundary. Their absence
  is described as a usually useful gap, while an absent DPE is marked definitely
  expected without making a legal-mandatory claim.

These boundaries live in small pure functions with unit tests so they can evolve from
real document evaluations without changing extraction prompts.

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
- Structured analysis currently runs synchronously and retries are manual. Provider
  errors are stored as a generic failure reason; response content and full extracted
  document text are not written to application logs.
- Citation page numbers must exist in the Xberg output. A quote is retained only when
  it is an exact normalized substring; otherwise the scalar value must itself be found
  on that page and provenance falls back to page-only. This favors dropping a fact over
  accepting an unverifiable claim.
