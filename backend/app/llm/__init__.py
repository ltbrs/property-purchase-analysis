"""Hosted structured-output client boundary."""

from app.llm.structured_output import (
    OPENAI_MODEL,
    StructuredOutputClient,
    StructuredOutputClientDependency,
    StructuredOutputResult,
    get_structured_output_client,
)

__all__ = [
    "OPENAI_MODEL",
    "StructuredOutputClient",
    "StructuredOutputClientDependency",
    "StructuredOutputResult",
    "get_structured_output_client",
]
