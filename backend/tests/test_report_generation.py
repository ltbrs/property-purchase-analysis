from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.reports import build_buyer_report
from app.risks.models import (
    DocumentExpectation,
    FindingStatus,
    MissingDocumentReason,
    RiskCategory,
    RiskFinding,
    RiskSeverity,
)
from tests.test_risk_engine import dpe_facts


def test_report_orders_sections_enriches_sources_and_keeps_uncertainty() -> None:
    document_id = uuid4()
    dpe = dpe_facts(rating="B")
    assert dpe.dpe_rating.source is not None
    source = dpe.dpe_rating.source.model_copy(update={"document_id": document_id})
    dpe = dpe.model_copy(
        update={"dpe_rating": dpe.dpe_rating.model_copy(update={"source": source})}
    )
    findings = [
        RiskFinding(
            code="FINANCIAL_TEST",
            finding_key="FINANCIAL_TEST",
            category=RiskCategory.FINANCIAL,
            title="Coût identifié",
            severity=RiskSeverity.HIGH,
            description="Une dépense explicite est indiquée.",
            status=FindingStatus.CONFIRMED,
            amount_eur=Decimal("5000"),
            sources=[source],
        ),
        RiskFinding(
            code="MISSING_TEST",
            finding_key="MISSING_TEST",
            category=RiskCategory.MISSING_INFORMATION,
            title="Pièce absente",
            severity=RiskSeverity.MEDIUM,
            description="La pièce n’a pas été fournie.",
            status=FindingStatus.MISSING_INFORMATION,
            expectation_level=DocumentExpectation.CONTEXT_DEPENDENT,
            missing_reason=MissingDocumentReason.ABSENT,
        ),
    ]

    report = build_buyer_report(
        analysis_case_id=uuid4(),
        title="Appartement test",
        findings=findings,
        document_names={document_id: "dpe.pdf"},
        dpe_documents=[dpe],
        diagnostics=[],
        generated_at=datetime(2026, 8, 26, tzinfo=UTC),
    )

    assert [section.code.value for section in report.sections] == [
        "financial",
        "building_coproperty",
        "energy",
        "diagnostics_safety",
        "inconsistencies",
        "missing_information",
        "reassuring",
    ]
    assert report.sections[0].findings[0].sources[0].document_name == "dpe.pdf"
    assert report.sections[5].findings[0].expectation_level == (
        DocumentExpectation.CONTEXT_DEPENDENT
    )
    assert report.sections[6].findings[0].title == "Classe énergétique B"
    assert report.summary.high_or_critical_count == 1
    assert report.summary.missing_information_count == 1
    assert report.summary.reassuring_count == 1
