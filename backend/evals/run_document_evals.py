import argparse
import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.documents.classification.models import DocumentClassificationCandidate, DocumentType
from app.documents.classification.prompts import CLASSIFICATION_SYSTEM_PROMPT
from app.documents.classification.service import MIN_KNOWN_TYPE_CONFIDENCE
from app.llm.structured_output import OpenAIStructuredOutputClient
from app.property.normalization.dpe import DpeExtractionCandidate, normalize_dpe_candidate
from app.property.normalization.dpe_prompts import DPE_EXTRACTION_SYSTEM_PROMPT

FIXTURES = Path(__file__).parent / "fixtures"
EVAL_DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000001")


def numbered_pages(pages: list[str]) -> str:
    return "\n\n".join(
        f'<page number="{index}">\n{text}\n</page>' for index, text in enumerate(pages, start=1)
    )


def load_fixtures(name: str) -> list[dict[str, Any]]:
    with (FIXTURES / f"{name}.json").open(encoding="utf-8") as fixture_file:
        value = json.load(fixture_file)
    if not isinstance(value, list):
        raise ValueError("Evaluation fixture root must be a list")
    return value


async def run_classification(client: OpenAIStructuredOutputClient) -> int:
    failures = 0
    for fixture in load_fixtures("classification"):
        result = await client.parse(
            system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
            user_content=numbered_pages(fixture["pages"]),
            response_model=DocumentClassificationCandidate,
        )
        actual = result.output.document_type
        if result.output.confidence < MIN_KNOWN_TYPE_CONFIDENCE:
            actual = DocumentType.UNKNOWN
        expected = fixture["expected_document_type"]
        passed = actual.value == expected
        failures += not passed
        outcome = "PASS" if passed else f"FAIL expected={expected} actual={actual.value}"
        print(f"{fixture['id']}: {outcome}")
    return failures


async def run_dpe(client: OpenAIStructuredOutputClient) -> int:
    failures = 0
    for fixture in load_fixtures("dpe"):
        pages = fixture["pages"]
        result = await client.parse(
            system_prompt=DPE_EXTRACTION_SYSTEM_PROMPT,
            user_content=numbered_pages(pages),
            response_model=DpeExtractionCandidate,
        )
        facts = normalize_dpe_candidate(
            result.output,
            document_id=EVAL_DOCUMENT_ID,
            pages={index: text for index, text in enumerate(pages, start=1)},
        ).model_dump(mode="json")
        mismatches = {
            name: {"expected": expected, "actual": facts[name]["value"]}
            for name, expected in fixture["expected"].items()
            if facts[name]["value"] != expected
        }
        passed = not mismatches
        failures += not passed
        print(f"{fixture['id']}: {'PASS' if passed else f'FAIL {mismatches}'}")
    return failures


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", choices=("classification", "dpe"))
    arguments = parser.parse_args()
    api_key = get_settings().openai_api_key
    if api_key is None:
        parser.error("OPENAI_API_KEY is not configured")
    client = OpenAIStructuredOutputClient(api_key.get_secret_value())
    if arguments.suite == "classification":
        return await run_classification(client)
    return await run_dpe(client)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
