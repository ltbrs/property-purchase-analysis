# Document extraction evaluations

These version-controlled golden fixtures are intentionally separate from unit tests.
They measure provider behavior against representative extracted French property text.
No PDF or personal data is sent unless the evaluator is run explicitly.

Run a suite from `backend/` with `OPENAI_API_KEY` configured:

```bash
uv run python -m evals.run_document_evals classification
uv run python -m evals.run_document_evals dpe
uv run python -m evals.run_document_evals ag_minutes
uv run python -m evals.run_document_evals financials
uv run python -m evals.run_document_evals diagnostics
```

The runner uses the same prompts, structured schemas, deterministic confidence threshold,
normalization, and fixed `gpt-5.6-luna` adapter as production. It prints fixture identifiers and
field-level mismatches without logging the fixture document text.
