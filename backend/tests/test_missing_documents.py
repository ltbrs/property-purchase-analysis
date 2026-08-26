from datetime import date
from uuid import uuid4

from app.documents.classification.models import DocumentType
from app.property.normalization.ag_minutes import NormalizedAgMinutes
from app.risks.models import DocumentExpectation, MissingDocumentReason
from app.risks.rules.missing_documents import (
    AvailableDocument,
    MissingDocumentContext,
    evaluate_missing_documents,
)


def test_empty_case_distinguishes_expected_and_useful_documents() -> None:
    findings = evaluate_missing_documents(
        available_documents=[],
        dpe_documents=[],
        minutes=[],
        financials=[],
        as_of=date(2026, 8, 26),
    )
    by_code = {finding.code: finding for finding in findings}

    assert by_code["MISSING_DPE_DOCUMENT"].expectation_level == (
        DocumentExpectation.DEFINITELY_EXPECTED
    )
    assert by_code["MISSING_DPE_DOCUMENT"].missing_reason == MissingDocumentReason.ABSENT
    assert by_code["MISSING_RECENT_AG_MINUTES"].expectation_level == (
        DocumentExpectation.USUALLY_USEFUL
    )
    assert by_code["MISSING_COPROPERTY_FINANCIALS"].expectation_level == (
        DocumentExpectation.USUALLY_USEFUL
    )
    assert all("obligatoire" not in finding.description.casefold() for finding in findings)


def test_classified_but_unprocessed_documents_are_insufficient() -> None:
    available = [
        AvailableDocument(
            document_id=uuid4(),
            document_type=DocumentType.DPE,
            document_date=date(2025, 1, 1),
        ),
        AvailableDocument(
            document_id=uuid4(),
            document_type=DocumentType.AG_MINUTES,
            document_date=date(2025, 5, 1),
        ),
        AvailableDocument(
            document_id=uuid4(),
            document_type=DocumentType.CHARGES,
            covered_period_end=date(2025, 12, 31),
        ),
    ]
    findings = evaluate_missing_documents(
        available_documents=available,
        dpe_documents=[],
        minutes=[NormalizedAgMinutes(meeting_date=date(2025, 5, 1), items=[])],
        financials=[],
        as_of=date(2026, 8, 26),
    )
    by_code = {finding.code: finding for finding in findings}

    assert by_code["INSUFFICIENT_DPE_DOCUMENT"].missing_reason == (
        MissingDocumentReason.INSUFFICIENT
    )
    assert by_code["INSUFFICIENT_COPROPERTY_FINANCIALS"].missing_reason == (
        MissingDocumentReason.INSUFFICIENT
    )
    assert "MISSING_RECENT_AG_MINUTES" not in by_code
    assert "INSUFFICIENT_RECENT_AG_MINUTES" not in by_code


def test_ag_recency_boundary_is_inclusive() -> None:
    document_id = uuid4()
    at_boundary = AvailableDocument(
        document_id=document_id,
        document_type=DocumentType.AG_MINUTES,
        document_date=date(2023, 8, 26),
    )
    old = at_boundary.model_copy(update={"document_date": date(2023, 8, 25)})

    boundary_codes = {
        finding.code
        for finding in evaluate_missing_documents(
            available_documents=[at_boundary],
            dpe_documents=[],
            minutes=[],
            financials=[],
            as_of=date(2026, 8, 26),
        )
    }
    old_codes = {
        finding.code
        for finding in evaluate_missing_documents(
            available_documents=[old],
            dpe_documents=[],
            minutes=[],
            financials=[],
            as_of=date(2026, 8, 26),
        )
    }

    assert "INSUFFICIENT_RECENT_AG_MINUTES" not in boundary_codes
    assert "INSUFFICIENT_RECENT_AG_MINUTES" in old_codes


def test_coproperty_documents_are_not_expected_for_known_non_coproperty() -> None:
    findings = evaluate_missing_documents(
        available_documents=[],
        dpe_documents=[],
        minutes=[],
        financials=[],
        as_of=date(2026, 8, 26),
        context=MissingDocumentContext(is_coproperty=False),
    )

    assert {finding.code for finding in findings} == {"MISSING_DPE_DOCUMENT"}
