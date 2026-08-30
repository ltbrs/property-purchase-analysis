# AGENTS.md

## Product

This repository contains a SaaS for home buyers in France.

Users upload property documents such as DPEs, diagnostics, copropriété AG minutes, charges, works, and financial statements. The application extracts factual information, applies deterministic real-estate risk rules, and produces a source-backed report highlighting risks, future costs, inconsistencies, and missing information.

The product is decision support, not legal, notarial, engineering, energy-audit, or financial advice.

## Core engineering principles

Optimize for:

1. correctness over cleverness
2. traceability over fluent answers
3. deterministic rules over LLM judgment when rules can be encoded
4. simple architecture over premature infrastructure
5. explicit uncertainty over invented conclusions
6. fast iteration over hypothetical scalability

Every important user-facing finding should be traceable to its source document and page whenever technically possible.

Never fabricate facts that are absent from the uploaded documents.

## MVP architecture

Use:

- Next.js + TypeScript for the frontend
- FastAPI + Python + Pydantic for the backend + uv
- PostgreSQL, preferably Supabase for the MVP
- S3-compatible object storage for PDFs
- Xberg as the default PDF parser
- one hosted LLM with structured outputs
- vision only as a fallback for poorly extracted or scanned pages

Do not add by default:

- LangChain
- LlamaIndex
- vector databases
- Elasticsearch
- Kafka
- Kubernetes
- Celery
- Temporal
- microservices
- multi-agent orchestration

Introduce infrastructure only when real production needs justify it.

## Processing architecture

Keep the workflow explicit:

```text
PDF upload
→ file validation
→ PDF extraction
→ document classification
→ structured extraction
→ normalized property model
→ deterministic risk rules
→ cross-document checks
→ LLM explanation
→ source-backed report
```

Avoid hiding the full workflow behind one autonomous agent.

## LLM policy

Use LLMs for:

- understanding document wording
- structured fact extraction
- classification
- normalization
- cross-document interpretation
- concise explanations

Use deterministic code for:

- arithmetic
- dates
- thresholds
- financial totals
- permissions
- billing
- risk severity when rules exist
- legal or regulatory conditions once encoded

Persist structured outputs only after validation.

Allow `null`, `unknown`, `not_found`, and `ambiguous` when appropriate.

Never force certainty.

## Provenance

Important extracted facts and risks should retain:

- source document ID
- page number when available
- short quote only when useful

A risk without document-backed evidence should be clearly distinguished from a confirmed risk.

## Domain model

Prefer a stable normalized internal model over passing raw LLM outputs around.

Likely domains:

```text
property
sale
energy
coproperty
financials
works
building
diagnostics
legal
environmental_risks
documents
```

Evolve the schema from real documents rather than designing an exhaustive model upfront.

## Risk engine

The core product value is the risk model.

When adding a risk:

- define a stable risk code
- define required facts
- implement deterministic detection when possible
- define severity explicitly
- preserve source references
- handle missing and conflicting information
- add tests

The product must distinguish:

- confirmed facts
- inferred risks
- missing information
- inconsistencies

## Testing and evaluation

Use `pytest` for backend tests.

Test:

- normalization
- risk rules
- parsers/adapters
- cross-document reconciliation
- API behavior

LLM behavior should use dedicated evaluation fixtures, not only unit tests.

Maintain a small golden dataset with representative French property documents.

Measure at least:

- extraction correctness
- monetary amount accuracy
- date accuracy
- citation accuracy
- risk recall
- false-positive rate

## Security and privacy

Property documents may contain personal data.

Requirements:

- private object storage
- server-side authorization
- signed URLs where appropriate
- no public buckets
- no full documents in logs
- no full extracted text in ordinary logs
- document deletion support
- clear control over which third-party providers receive document content

## Frontend principles

The core UX is a structured report, not a chatbot.

Prioritize:

1. major financial risks
2. building and copropriété risks
3. energy risks
4. diagnostics and safety
5. inconsistencies
6. missing documents or questions to ask
7. reassuring findings

Each finding should show its source.

The product should feel like a trustworthy inspection report, not an AI demo.
In the UI, never set accent border.

## Dependency policy

Before adding a dependency, ask:

1. does the framework or standard library already solve this?
2. is the dependency actively maintained?
3. does it materially reduce complexity?
4. can this be implemented simply without it?

Prefer explicit application code over generic abstractions that may be useful later.

## Scope

The MVP should answer one question very well:

> Based on the documents provided for this property, what important risks, future costs, inconsistencies, and missing information should the buyer know before purchasing?

Protect that scope until real usage demonstrates a better adjacent opportunity.
