# Step-by-step implementation prompts

Use these prompts sequentially. Each prompt assumes the previous steps are already implemented.

Before every step:

- read `AGENTS.md`
- inspect the existing code
- preserve the current architecture
- do not introduce unrelated infrastructure
- add tests for deterministic business logic
- update documentation when behavior changes

---

## Step 1 — Domain model and persistence

Implement the first stable internal domain model and persistence layer.

The goal is to represent:

- users
- analysis cases
- properties
- uploaded documents
- document processing state
- source references
- extracted facts
- risks
- reports

Keep the schema intentionally small.

Create typed Pydantic/domain models and the minimum PostgreSQL persistence needed.

Important rules:

- PDFs are stored in object storage, not PostgreSQL
- important facts must support provenance
- support missing and ambiguous values explicitly
- do not model every possible French real-estate concept yet
- migrations must be included
- keep database access simple and explicit

Add tests for model validation and persistence boundaries.

At the end, explain the schema and what was intentionally deferred.

---

## Step 2 — File upload and document storage

Implement document upload for an analysis case.

Requirements:

- accept PDFs only for now
- validate MIME type and file size
- store PDFs in private S3-compatible object storage
- persist document metadata in PostgreSQL
- enforce server-side ownership
- expose processing status
- make upload idempotent where practical

Suggested states:

```text
uploaded
extracting
extracted
analyzing
completed
failed
```

Do not parse documents yet.

Frontend:

- create a clean upload flow
- show uploaded documents
- show current status
- handle upload failures clearly

Add tests around authorization, validation, and metadata persistence.

---

## Step 3 — Xberg PDF extraction

Implement the first PDF extraction adapter using Xberg.

The parser should extract, when possible:

- text
- page boundaries
- tables
- metadata

Wrap Xberg behind an internal parser interface so it can be replaced or supplemented later without affecting the domain code.

Persist extraction output in a form suitable for later structured extraction.

Requirements:

- preserve page-level provenance
- do not flatten away page numbers
- handle parser failures cleanly
- record parser name/version where practical
- collect extraction duration
- do not add a second parser yet

Create fixtures with representative PDFs and add parser integration tests.

At the end, document known extraction limitations.

---

## Step 4 — Document classification

Implement document classification.

Initial document types:

```text
dpe
ag_minutes
diagnostics
copro_financials
charges
works_call
property_tax
copro_rules
maintenance_log
risk_statement
unknown
```

Classification output must contain:

- document type
- confidence
- optional date or covered period
- optional issuer
- extraction strategy if relevant

Use the primary LLM with structured output.

Requirements:

- validate model responses
- do not force a known category when confidence is low
- store `unknown` when appropriate
- persist model/version metadata
- add an evaluation fixture set
- keep prompts version-controlled

Do not perform full fact extraction yet.

---

## Step 5 — DPE structured extraction

Implement the first real domain extractor: DPE.

Extract only facts that are useful for buyer-risk analysis.

Likely fields:

```text
dpe_rating
ges_rating
energy_consumption_kwh_m2_year
estimated_annual_energy_cost_min
estimated_annual_energy_cost_max
surface
heating_type
hot_water_type
dpe_date
dpe_valid_until
recommendations
```

Every important fact must retain source provenance.

Requirements:

- use structured LLM output
- preserve `null` for missing data
- do not infer values that are absent
- validate dates and numeric ranges in code
- add deterministic normalization
- add evaluation fixtures for several DPE formats
- test source/page attribution

Do not generate user-facing risks yet.

---

## Step 6 — First deterministic risk engine

Implement the first deterministic risk engine.

Start only with DPE-related rules.

Examples:

- poor energy rating
- high energy consumption
- unusually high projected annual energy cost
- DPE validity issues
- missing critical DPE information

Each risk must contain:

```text
code
category
title
severity
description
status
confidence if relevant
amount_eur if relevant
sources
```

The engine should consume normalized facts, not raw PDF text.

Requirements:

- stable risk codes
- unit tests for every rule
- explicit boundary conditions
- deterministic severity
- no LLM judgment inside rule evaluation

Use the LLM only to produce concise explanations after the risk is detected.

---

## Step 7 — AG minutes extraction

Implement structured extraction for copropriété AG minutes.

Focus on buyer-relevant information:

- voted works
- planned or discussed works
- façade
- roof
- elevator
- heating
- water infiltration
- structural issues
- major maintenance
- legal disputes
- unpaid charges
- exceptional expenses
- repeated unresolved issues

For each extracted item, retain:

- meeting date
- resolution reference if available
- status
- amount
- property share amount when explicitly available
- source page

Do not estimate missing property-share costs unless there is enough deterministic data to calculate them.

Create evaluation fixtures across several AG formats.

---

## Step 8 — Works and copropriété risk rules

Extend the deterministic risk engine with copropriété rules.

Examples:

- major works already voted
- high property-share cost
- major works repeatedly discussed but not yet voted
- recurring water infiltration
- repeated façade or roof issues
- significant unpaid charges
- litigation or serious copropriété disputes

Distinguish:

```text
confirmed
likely
possible
missing_information
```

Do not label discussed works as voted works.

Add unit tests for all rule conditions and edge cases.

---

## Step 9 — Multi-document timeline and reconciliation

Implement cross-document reconciliation.

The goal is to create timelines and detect inconsistencies across documents.

Examples:

- a project appears in one AG and disappears later
- voted works should correlate with later funding calls
- an issue is discussed repeatedly over multiple years
- reported heating type differs across documents
- property surface differs across DPE / Carrez / sale documents
- financial values contradict one another

Operate on normalized facts.

Do not use raw full-document retrieval as the primary reconciliation mechanism.

Store inconsistencies as typed findings with provenance from all relevant documents.

---

## Step 10 — Financial and charges extraction

Add structured extraction for:

- copropriété financial statements
- annual charges
- exceptional charges
- travaux fund
- appels de fonds
- unpaid copropriété charges where available

Normalize monetary values and covered periods.

Implement deterministic calculations for:

- annual charge evolution
- exceptional expenses
- material increases
- known upcoming payments
- potential buyer exposure where source data is explicit

Never rely on LLM arithmetic.

Add tests for monetary normalization and date-period comparisons.

---

## Step 11 — Diagnostics and environmental risks

Add support for the most useful additional diagnostic documents.

Prioritize:

- asbestos
- lead
- electrical installation
- gas installation
- ERP / environmental risks
- Carrez measurement

Implement typed extraction and deterministic rules only where the meaning is clear.

Do not try to encode every legal nuance at once.

When legal interpretation is uncertain, surface the factual finding and explicit uncertainty rather than presenting legal advice.

---

## Step 12 — Missing-document detection

Implement missing-document analysis.

Given the known property and sale context, identify which expected documents are absent or insufficient.

The output should distinguish:

- definitely expected
- usually useful
- context-dependent

Example findings:

- no recent AG minutes
- no DPE
- no copropriété financial information
- missing supporting document for mentioned works

Do not imply a document is legally mandatory unless the rule is explicitly encoded and verified.

---

## Step 13 — Report generation

Implement the first complete buyer-facing report.

The report should prioritize:

1. major financial risks
2. building / copropriété risks
3. energy risks
4. diagnostics and safety
5. inconsistencies
6. missing information
7. reassuring findings

Each finding should show:

- severity
- concise title
- concise explanation
- amount when known
- status / uncertainty
- source document
- page

The LLM may rewrite deterministic findings into concise user-friendly language, but may not invent new facts.

Make the report useful without a chatbot.

---

## Step 14 — Source inspection UX

Improve trust and traceability.

From every finding, users should be able to inspect the source.

Implement:

- source document link
- page navigation
- highlighted or extracted source context where practical
- secure access via signed/private URLs

Avoid storing unnecessary long quotes.

The user should be able to understand why a risk exists without trusting the AI blindly.

---

## Step 15 — Vision fallback

Introduce a vision fallback only for pages that fail normal extraction.

Define explicit triggers, for example:

- near-empty extraction on a non-empty page
- scan-only page
- malformed table extraction
- low-confidence required-field extraction

Pipeline:

```text
Xberg
→ detect extraction problem
→ render page image
→ vision model
→ structured page extraction
→ merge with normal extraction
```

Requirements:

- page-level fallback only
- track model usage and cost
- preserve provenance
- avoid sending whole documents to vision by default
- evaluate whether it materially improves extraction quality

Do not add Docling unless the evaluation demonstrates a concrete need.

---

## Step 16 — Processing jobs and retries

Move PDF parsing and LLM analysis into background jobs if synchronous processing has become inconvenient.

Requirements:

- simple job abstraction
- idempotent tasks
- retry policies
- status transitions
- useful errors
- no distributed workflow engine

Prefer a lightweight queue backed by existing infrastructure or a small managed service.

Do not add Celery or Temporal by reflex.

---

## Step 17 — Cost and observability

Add minimal production observability.

Track per analysis case:

```text
page count
parser duration
LLM calls
input tokens
output tokens
vision calls
retries
total analysis duration
estimated AI cost
```

Track failures without logging sensitive document content.

Build a small internal view or query that makes cost per case visible.

Use this data before optimizing architecture.

---

## Step 18 — Golden dataset and evaluation harness

Build a reusable evaluation harness.

Create a golden dataset with representative and difficult French property documents:

- native PDFs
- scanned PDFs
- tables
- multi-column documents
- long AG minutes
- poor OCR
- mixed-format diagnostics

Evaluate:

- classification
- field extraction
- monetary values
- dates
- provenance accuracy
- risk detection
- false positives

Keep evaluation separate from normal unit tests.

Produce a concise evaluation report that makes regressions visible.

---

## Step 19 — Security and privacy hardening

Perform a dedicated security pass.

Verify:

- tenant/user isolation
- private document storage
- signed URL behavior
- upload restrictions
- document deletion
- log redaction
- secret handling
- third-party provider exposure
- authorization on every document and case endpoint

Add tests for cross-user access attempts.

Do not proceed with production deployment until these checks pass.

---

## Step 20 — MVP polish and deployment

Prepare the MVP for real users.

Tasks:

- clean onboarding
- stable upload flow
- meaningful processing states
- useful report empty/error states
- mobile-responsive layout
- clear product disclaimer
- document deletion controls
- production environment setup
- database migrations
- object storage config
- frontend deployment
- backend deployment
- error monitoring
- analytics only if useful

Run the complete evaluation suite and core test suite before deployment.

At the end, produce:

1. production architecture summary
2. operational checklist
3. known limitations
4. measured extraction/risk quality
5. measured average cost per analysis
6. highest-priority post-MVP improvements
