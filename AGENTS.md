# AGENTS.md

## Product and scope

Build decision-support software for French home buyers. It extracts facts from property documents and produces a source-backed report of important risks, future costs, inconsistencies, and missing information.

It is not legal, notarial, engineering, energy-audit, or financial advice. Do not expand the MVP beyond this purpose without evidence from real usage.

## Non-negotiable principles

- Prioritize correctness, traceability, explicit uncertainty, and simple architecture.
- Never invent facts absent from uploaded documents.
- Cite the source document and page for important facts and findings whenever possible.
- Prefer deterministic rules to LLM judgment when rules can be encoded.
- Validate structured LLM output before persistence. Permit `null`, `unknown`, `not_found`, and `ambiguous`.
- Keep confirmed facts, inferred risks, missing information, and inconsistencies distinct.

## Architecture

- Frontend: Next.js and TypeScript.
- Backend: FastAPI, Python, Pydantic, `uv`, and `pytest`.
- Data: PostgreSQL, preferably Supabase for the MVP.
- Files: private S3-compatible object storage.
- Documents: Xberg by default, with vision only for poorly extracted or scanned pages.
- AI: one hosted LLM with structured outputs.

Keep processing explicit:

```text
upload → validation → extraction → classification → structured extraction
→ normalized property model → deterministic risks → cross-document checks
→ LLM explanation → source-backed report
```

Use LLMs for language understanding, classification, structured extraction, normalization, cross-document interpretation, and concise explanations. Use deterministic code for arithmetic, dates, thresholds, totals, permissions, billing, risk severity, and encoded legal or regulatory conditions.

Prefer a stable normalized model based on real documents. Do not pass raw LLM output through the application or design an exhaustive schema prematurely.

Do not add LangChain, LlamaIndex, vector databases, Elasticsearch, Kafka, Kubernetes, Celery, Temporal, microservices, or multi-agent orchestration without a demonstrated production need. Prefer standard-library or framework features and explicit application code before new dependencies.

## Findings and risk rules

Every important extracted fact or risk should retain its source document ID, page when available, and a short quote only when useful. Clearly label findings without documentary evidence as inferred, not confirmed.

For each risk rule:

- define a stable code, required facts, and explicit severity;
- use deterministic detection when possible;
- preserve sources and handle missing or conflicting information;
- add tests.

## Testing

Test normalization, risk rules, parser adapters, cross-document reconciliation, and API behavior. Test LLM behavior with evaluation fixtures and maintain a small golden set of representative French property documents.

Track extraction, monetary, date, and citation accuracy, plus risk recall and false-positive rate.

## Security and privacy

- Enforce server-side authorization and private object storage.
- Use signed URLs where appropriate and never use public buckets.
- Do not log full documents or full extracted text in ordinary logs.
- Support document deletion.
- Make clear which third-party providers receive document content.

## Frontend

The main UX is a trustworthy inspection report, not a chatbot or AI demo. Prioritize financial, building, copropriété, energy, diagnostic, and safety risks, followed by inconsistencies, missing information, and reassuring findings. Show a source for each finding.

Never set an accent border in the UI.

## Style

Do not use an em dash, an en dash as an aside, or a double hyphen as punctuation. Rewrite with a comma, parentheses, a colon, or two sentences. List bullets and dashes between a bold label and its gloss are allowed.
