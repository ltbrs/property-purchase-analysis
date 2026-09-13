import asyncio
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from app.llm import structured_output


class ExampleOutput(BaseModel):
    value: str


class FakeResponses:
    def __init__(self) -> None:
        self.request: dict[str, Any] | None = None

    async def parse(self, **request: Any) -> SimpleNamespace:
        self.request = request
        return SimpleNamespace(
            output_parsed=ExampleOutput(value="ok"),
            id="resp_test",
            model="gpt-5.6-luna-2026-08-01",
        )


class FakeOpenAI:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_parse_attaches_user_and_document_metadata(monkeypatch: Any) -> None:
    fake_openai = FakeOpenAI()
    monkeypatch.setattr(structured_output, "AsyncOpenAI", lambda *, api_key: fake_openai)
    client = structured_output.OpenAIStructuredOutputClient("test-key")
    user_id = uuid4()
    document_id = uuid4()

    result = asyncio.run(
        client.parse(
            system_prompt="Return a structured result.",
            user_content="Test document",
            response_model=ExampleOutput,
            user_id=user_id,
            document_id=document_id,
        )
    )

    assert result.output == ExampleOutput(value="ok")
    assert fake_openai.responses.request is not None
    assert fake_openai.responses.request["metadata"] == {
        "user_id": str(user_id),
        "document_id": str(document_id),
    }
