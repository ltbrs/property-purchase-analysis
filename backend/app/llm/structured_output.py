from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Protocol, TypeVar
from uuid import UUID

from fastapi import Depends, HTTPException, status
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import get_settings

OPENAI_MODEL = "gpt-6-luna"

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


@dataclass(frozen=True)
class StructuredOutputResult[OutputModel: BaseModel]:
    output: OutputModel
    response_id: str
    requested_model: str
    resolved_model: str
    input_tokens: int = 0
    output_tokens: int = 0


class StructuredOutputClient(Protocol):
    async def parse(
        self,
        *,
        system_prompt: str,
        user_content: str,
        response_model: type[StructuredModel],
        user_id: UUID,
        document_id: UUID,
    ) -> StructuredOutputResult[StructuredModel]: ...


class OpenAIStructuredOutputClient:
    """Narrow OpenAI adapter; domain services never depend on SDK response types."""

    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key, max_retries=0, timeout=get_settings().openai_timeout_seconds
        )

    async def parse(
        self,
        *,
        system_prompt: str,
        user_content: str,
        response_model: type[StructuredModel],
        user_id: UUID,
        document_id: UUID,
    ) -> StructuredOutputResult[StructuredModel]:
        response = await self._client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            text_format=response_model,
            max_output_tokens=16000,
            reasoning={"effort": "low"},
            metadata={
                "user_id": str(user_id),
                "document_id": str(document_id),
            },
            store=False,
        )
        if response.output_parsed is None:
            raise RuntimeError("OpenAI returned no structured output")
        usage = getattr(response, "usage", None)
        return StructuredOutputResult(
            output=response.output_parsed,
            response_id=response.id,
            requested_model=OPENAI_MODEL,
            resolved_model=response.model,
            input_tokens=usage.input_tokens if usage is not None else 0,
            output_tokens=usage.output_tokens if usage is not None else 0,
        )

    async def parse_image(
        self,
        *,
        system_prompt: str,
        user_content: str,
        image_url: str,
        response_model: type[StructuredModel],
        user_id: UUID,
        document_id: UUID,
    ) -> StructuredOutputResult[StructuredModel]:
        response = await self._client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user_content},
                        {"type": "input_image", "image_url": image_url, "detail": "high"},
                    ],
                },
            ],
            text_format=response_model,
            reasoning={"effort": "none"},
            max_output_tokens=16000,
            metadata={"user_id": str(user_id), "document_id": str(document_id)},
            store=False,
        )
        if response.output_parsed is None:
            raise RuntimeError("OpenAI returned no page transcription")
        return StructuredOutputResult(
            output=response.output_parsed,
            response_id=response.id,
            requested_model=OPENAI_MODEL,
            resolved_model=response.model,
            input_tokens=response.usage.input_tokens if response.usage is not None else 0,
            output_tokens=response.usage.output_tokens if response.usage is not None else 0,
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
