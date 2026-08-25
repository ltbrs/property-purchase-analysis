# Initial prompt — repository setup

You are setting up the initial repository for a SaaS that helps French home buyers identify risks before purchasing a property.

Read `AGENTS.md` first and follow it strictly.

The application will ingest documents such as:

- DPE
- diagnostics
- copropriété AG minutes
- copropriété financial statements
- charges
- appels de fonds
- voted or planned works
- règlement de copropriété
- maintenance log
- tax documents
- seller-provided documents

The target MVP architecture is:

```text
frontend: Next.js + TypeScript
backend: FastAPI + Python + Pydantic
database: PostgreSQL / Supabase
file storage: S3-compatible storage
PDF parser: Xberg
LLM: one hosted model with structured outputs
vision: fallback only
```

Do not introduce:

- LangChain
- LlamaIndex
- vector databases
- Elasticsearch
- Kafka
- Kubernetes
- Celery
- Temporal
- microservices
- generic multi-agent frameworks

## Goal of this task

Create the initial production-oriented monorepo skeleton and minimal developer setup, but do not implement product features yet.

## Required structure

Use a structure close to:

```text
/
  AGENTS.md
  README.md
  .gitignore
  .env.example
  docker-compose.yml

  frontend/
    app/
    components/
    features/
    lib/

  backend/
    app/
      api/
      core/
      documents/
        parsers/
        classification/
        extraction/
      property/
        models/
        normalization/
      risks/
        models/
        rules/
        engine/
      reports/
      llm/
      storage/
      jobs/
    tests/
```

Adapt only when the framework strongly benefits from a slightly different structure.

## Frontend requirements

Initialize a modern Next.js app with:

- TypeScript
- App Router
- linting
- a simple styling approach
- no unnecessary state management
- no unnecessary component library unless clearly justified

Create only:

- a minimal landing page
- a minimal application shell
- placeholder routes for upload and analysis

Do not design the final UI yet.

## Backend requirements

Initialize FastAPI with:

- Pydantic settings
- structured config
- health endpoint
- API router organization
- pytest
- linting / formatting
- typed code

Create placeholder domain modules only.

Do not implement fake business logic.

## Local development

Add a minimal Docker Compose setup for PostgreSQL if useful.

Document:

- how to start frontend
- how to start backend
- how to run tests
- required environment variables
- expected local ports

## Environment variables

Create `.env.example` with placeholders for likely requirements such as:

```text
DATABASE_URL=
OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
LLM_API_KEY=
```

Do not hardcode a specific LLM provider unless the code needs one now.

## Quality requirements

Before finishing:

- run frontend lint/type checks
- run backend tests
- run backend lint/type checks if configured
- fix obvious setup issues
- keep dependencies minimal
- verify README instructions match the actual commands

## Output

At the end, summarize:

1. repository structure created
2. key dependencies added
3. commands to run the project
4. intentional omissions for later steps
5. any decisions that deviate from this prompt and why
