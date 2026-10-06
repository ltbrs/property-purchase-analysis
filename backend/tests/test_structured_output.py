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
            model="gpt-6-luna-2026-08-01",
            usage=None,
        )


class FakeOpenAI:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_parse_attaches_user_and_document_metadata(monkeypatch: Any) -> None:
    fake_openai = FakeOpenAI()
    monkeypatch.setattr(structured_output, "AsyncOpenAI", lambda **kwargs: fake_openai)
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
    assert fake_openai.responses.request["store"] is False
    assert fake_openai.responses.request["metadata"] == {
        "user_id": str(user_id),
        "document_id": str(document_id),
    }


def test_vision_uses_luna_image_structured_output_and_no_sdk_retries(monkeypatch: Any) -> None:
    fake_openai = FakeOpenAI()
    options: dict[str, Any] = {}

    def create_client(**kwargs: Any) -> FakeOpenAI:
        options.update(kwargs)
        return fake_openai

    monkeypatch.setattr(structured_output, "AsyncOpenAI", create_client)
    client = structured_output.OpenAIStructuredOutputClient("test-key")
    asyncio.run(
        client.parse_image(
            system_prompt="Transcris uniquement le contenu lisible.",
            user_content="Page 2",
            image_url="data:image/png;base64,test",
            response_model=ExampleOutput,
            user_id=uuid4(),
            document_id=uuid4(),
        )
    )
    request = fake_openai.responses.request
    assert request is not None
    assert options["max_retries"] == 0
    assert request["model"] == "gpt-6-luna"
    assert request["store"] is False
    assert request["text_format"] is ExampleOutput
    assert request["reasoning"] == {"effort": "none"}
    assert request["input"][1]["content"][1]["type"] == "input_image"
    assert request["input"][1]["content"][1]["detail"] == "high"
