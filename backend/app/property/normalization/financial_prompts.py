FINANCIAL_EXTRACTION_PROMPT_VERSION = "copro-financials-v1"

FINANCIAL_EXTRACTION_SYSTEM_PROMPT = """
Extract only explicit copropriété financial facts useful to a buyer: annual charges, exceptional
charges, works fund, funding calls, and unpaid copropriété charges. Copy monetary values exactly as
printed; never add, subtract, prorate, or estimate. Distinguish the copropriété total from the lot's
property-share amount and populate the latter only when explicit. Use ISO dates for covered periods
and due dates. Relate a funding call to a project only when named. Every item must cite its
one-based page and a short verbatim quote. Return null for absent or ambiguous values.
""".strip()
