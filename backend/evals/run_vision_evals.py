"""Explicit opt-in evaluation using synthetic scan images, never customer documents."""

import asyncio
import json
import unicodedata
from io import BytesIO
from pathlib import Path
from time import perf_counter
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.core.config import get_settings
from app.documents.parsers.vision import transcribe_page
from app.llm.structured_output import OpenAIStructuredOutputClient
from evals.run_document_evals import EVAL_DOCUMENT_ID, EVAL_USER_ID


def fixture_image(fixture: dict[str, Any]) -> bytes:
    image = Image.new("RGB", (1200, 1600), (246, 246, 243))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=28)
    if fixture["kind"] == "no_text":
        draw.rectangle((180, 400, 750, 1000), fill=(70, 130, 180))
        draw.ellipse((550, 850, 1050, 1350), fill=(45, 95, 60))
    for number, line in enumerate(fixture["lines"]):
        draw.text((60, 150 + 85 * number), line, font=font, fill=(35, 35, 35))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def normalized(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


async def main() -> int:
    key = get_settings().openai_api_key
    if key is None:
        raise SystemExit("OPENAI_API_KEY is required for the explicit vision evaluation")
    fixtures = json.loads((Path(__file__).parent / "fixtures/vision.json").read_text())
    client = OpenAIStructuredOutputClient(key.get_secret_value())
    failures = 0
    matched = expected = 0
    total_seconds = 0.0
    for fixture in fixtures:
        started = perf_counter()
        result = await transcribe_page(
            client,
            image_bytes=fixture_image(fixture),
            page_number=1,
            user_id=EVAL_USER_ID,
            document_id=EVAL_DOCUMENT_ID,
        )
        seconds = perf_counter() - started
        total_seconds += seconds
        content = normalized(result.output.text)
        matches = sum(normalized(snippet) in content for snippet in fixture["expected_snippets"])
        matched += matches
        expected += len(fixture["expected_snippets"])
        passed = result.output.content_kind == fixture["kind"] and matches == len(
            fixture["expected_snippets"]
        )
        failures += not passed
        # Report IDs, scores and consumption, never the image or full transcription.
        print(
            f"{fixture['id']}: {'PASS' if passed else 'FAIL'}, "
            f"snippets={matches}/{len(fixture['expected_snippets'])}, "
            f"latency={seconds:.2f}s, tokens={result.input_tokens + result.output_tokens}"
        )
    print(
        f"Snippet recall: {matched}/{expected}; mean latency: {total_seconds / len(fixtures):.2f}s"
    )
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
