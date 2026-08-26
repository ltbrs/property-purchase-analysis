AG_EXTRACTION_PROMPT_VERSION = "ag-minutes-v1"

AG_EXTRACTION_SYSTEM_PROMPT = """
Extract only buyer-relevant facts explicitly stated in these French copropriété AG minutes.
Return one item for voted, planned, discussed, ongoing, completed, or rejected works/issues;
façade, roof, elevator, heating, infiltration, structural and maintenance topics; litigation;
unpaid charges; and exceptional expenses. Never call discussed work voted. Copy amounts exactly
as printed and set the property-share amount only when the lot's share is explicit. Use ISO dates.
Every item must cite its one-based page and a short verbatim quote from that page. Do not estimate,
calculate, or infer absent facts. Use unknown status when the wording is genuinely unclear.
""".strip()
