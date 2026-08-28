DPE_EXTRACTION_PROMPT_VERSION = "dpe-extraction-v2"

DPE_EXTRACTION_SYSTEM_PROMPT = """Extract buyer-relevant facts from this French DPE.

Rules:
- Use only information explicitly present in the supplied numbered pages.
- Never calculate, estimate, complete, or infer a missing value.
- For every non-null fact, return its one-based page_number and a short exact quote from that page.
- If a value is missing or ambiguous, return value=null, page_number=null, quote=null.
- Dates must be ISO YYYY-MM-DD. If the exact day is absent, return null.
- Numeric values contain numbers only, in the units named by the schema.
- Ratings are a single A-G letter.
- Greenhouse-gas emissions are the explicit kg CO2e/m²/year value, not total kg CO2e/year.
- Annual energy costs are the DPE's explicit estimate, not bills or renovation costs.
- Surface is the explicitly stated reference/habitable surface used by the DPE.
- Recommendations must also have an exact page quote. Do not convert recommendations into risks.

The page markers are evidence boundaries, not document content."""
