from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Protocol, TypeVar

from fastapi import Depends, HTTPException, status
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import get_settings

OPENAI_MODEL = "gpt-5.6-luna"

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


@dataclass(frozen=True)
class StructuredOutputResult[OutputModel: BaseModel]:
    output: OutputModel
    response_id: str
    requested_model: str
    resolved_model: str


class StructuredOutputClient(Protocol):
    async def parse(
        self,
        *,
        system_prompt: str,
        user_content: str,
        response_model: type[StructuredModel],
    ) -> StructuredOutputResult[StructuredModel]: ...


class OpenAIStructuredOutputClient:
    """Narrow OpenAI adapter; domain services never depend on SDK response types."""

    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def parse(
        self,
        *,
        system_prompt: str,
        user_content: str,
        response_model: type[StructuredModel],
    ) -> StructuredOutputResult[StructuredModel]:
        response = await self._client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            text_format=response_model,
            store=True,
        )
        if response.output_parsed is None:
            raise RuntimeError("OpenAI returned no structured output")
        return StructuredOutputResult(
            output=response.output_parsed,
            response_id=response.id,
            requested_model=OPENAI_MODEL,
            resolved_model=response.model,
        )


@lru_cache
def get_structured_output_client() -> OpenAIStructuredOutputClient:
    api_key = get_settings().openai_api_key
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured",
        )
    return OpenAIStructuredOutputClient(api_key.get_secret_value())


StructuredOutputClientDependency = Annotated[
    StructuredOutputClient, Depends(get_structured_output_client)
]
