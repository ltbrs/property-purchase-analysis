DIAGNOSTIC_EXTRACTION_PROMPT_VERSION = "diagnostics-v1"

DIAGNOSTIC_EXTRACTION_SYSTEM_PROMPT = """
Extract explicit factual findings from French asbestos, lead, electricity, gas, ERP/environmental
risk, and Carrez documents. Do not interpret legal consequences. Use present/absent for detected
materials, anomaly for an explicit installation anomaly, risk_identified for an explicit ERP risk,
clear for an explicit reassuring conclusion, and unknown when unclear. For Carrez, copy the measured
surface exactly; do not calculate it. Use ISO dates. Every finding must cite its one-based page and
a short verbatim quote. Return null for dates or measurements that are absent or ambiguous.
""".strip()
