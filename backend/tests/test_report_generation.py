from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.property.normalization.dpe import (
    AdemeVerificationStatus,
    DpeAdemeVerification,
    DpeTextFact,
)
from app.reports import build_buyer_report
from app.risks.models import (
    DocumentExpectation,
    FindingReviewStatus,
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
    assert report.summary.finding_count == 2
    assert report.summary.analyzed_count == 2
    assert report.summary.risk_count == 1
    assert report.summary.high_or_critical_count == 1
    assert report.summary.missing_information_count == 1
    assert report.summary.reassuring_count == 1
    assert report.summary.risk_severity_counts == {
        RiskSeverity.INFO: 0,
        RiskSeverity.LOW: 0,
        RiskSeverity.MEDIUM: 0,
        RiskSeverity.HIGH: 1,
        RiskSeverity.CRITICAL: 0,
    }


def test_missing_information_is_not_counted_as_analyzed_or_as_a_strong_alert() -> None:
    missing_findings = [
        RiskFinding(
            code="MISSING_DPE_DOCUMENT",
            finding_key="MISSING_DPE_DOCUMENT",
            category=RiskCategory.MISSING_INFORMATION,
            title="DPE non fourni",
            severity=RiskSeverity.HIGH,
            description="Aucun DPE n'a été identifié.",
            status=FindingStatus.MISSING_INFORMATION,
            expectation_level=DocumentExpectation.DEFINITELY_EXPECTED,
            missing_reason=MissingDocumentReason.ABSENT,
        ),
        RiskFinding(
            code="MISSING_RECENT_AG_MINUTES",
            finding_key="MISSING_RECENT_AG_MINUTES",
            category=RiskCategory.MISSING_INFORMATION,
            title="PV d'AG non fournis",
            severity=RiskSeverity.MEDIUM,
            description="Aucun PV d'AG n'a été identifié.",
            status=FindingStatus.MISSING_INFORMATION,
            expectation_level=DocumentExpectation.USUALLY_USEFUL,
            missing_reason=MissingDocumentReason.ABSENT,
        ),
        RiskFinding(
            code="MISSING_COPROPERTY_FINANCIALS",
            finding_key="MISSING_COPROPERTY_FINANCIALS",
            category=RiskCategory.MISSING_INFORMATION,
            title="Informations financières absentes",
            severity=RiskSeverity.MEDIUM,
            description="Aucune information financière n'a été identifiée.",
            status=FindingStatus.MISSING_INFORMATION,
            expectation_level=DocumentExpectation.USUALLY_USEFUL,
            missing_reason=MissingDocumentReason.ABSENT,
        ),
    ]

    report = build_buyer_report(
        analysis_case_id=uuid4(),
        title="Appartement vide",
        findings=missing_findings,
        document_names={},
        dpe_documents=[],
        diagnostics=[],
    )

    assert report.summary.analyzed_count == 0
    assert report.summary.risk_count == 0
    assert report.summary.high_or_critical_count == 0
    assert report.summary.missing_information_count == 3
    assert all(count == 0 for count in report.summary.risk_severity_counts.values())


def test_user_can_reclassify_a_risk_as_a_reassuring_finding() -> None:
    reviewed_finding = RiskFinding(
        code="REVIEWED_TEST",
        finding_key="REVIEWED_TEST",
        category=RiskCategory.COPROPERTY,
        title="Travaux déjà budgétés",
        severity=RiskSeverity.HIGH,
        description="Le financement a été confirmé par l’utilisateur.",
        status=FindingStatus.CONFIRMED,
        review_status=FindingReviewStatus.NOT_PROBLEMATIC,
    )

    report = build_buyer_report(
        analysis_case_id=uuid4(),
        title="Appartement test",
        findings=[reviewed_finding],
        document_names={},
        dpe_documents=[],
        diagnostics=[],
    )

    reassuring = report.sections[-1].findings
    assert reassuring[0].finding_key == "REVIEWED_TEST"
    assert reassuring[0].analysis_type.value == "reassuring"
    assert reassuring[0].review_status == FindingReviewStatus.NOT_PROBLEMATIC
    assert report.summary.risk_count == 0
    assert report.summary.high_or_critical_count == 0
    assert report.summary.reassuring_count == 1


def test_uncertain_or_medium_findings_are_points_to_verify() -> None:
    finding = RiskFinding(
        code="VERIFY_TEST",
        finding_key="VERIFY_TEST",
        category=RiskCategory.DIAGNOSTICS,
        title="Information à confirmer",
        severity=RiskSeverity.MEDIUM,
        description="Le document ne permet pas de conclure définitivement.",
        status=FindingStatus.POSSIBLE,
    )

    report = build_buyer_report(
        analysis_case_id=uuid4(),
        title="Appartement test",
        findings=[finding],
        document_names={},
        dpe_documents=[],
        diagnostics=[],
    )

    report_finding = report.sections[3].findings[0]
    assert report_finding.analysis_type.value == "verification"
    assert report.summary.verification_count == 1
    assert report.summary.risk_count == 0


def test_report_exposes_verified_ademe_registration() -> None:
    document_id = uuid4()
    dpe = dpe_facts(rating="D")
    number_source = dpe.dpe_rating.source
    assert number_source is not None
    number_source = number_source.model_copy(update={"document_id": document_id})
    dpe = dpe.model_copy(
        update={
            "dpe_number": DpeTextFact(
                value="2475E4333306Q", source=number_source
            ),
            "ademe_verification": DpeAdemeVerification(
                status=AdemeVerificationStatus.VERIFIED,
                dpe_number="2475E4333306Q",
            ),
        }
    )

    report = build_buyer_report(
        analysis_case_id=uuid4(),
        title="Appartement test",
        findings=[],
        document_names={document_id: "DPE_D.pdf"},
        dpe_documents=[dpe],
        diagnostics=[],
    )

    reassuring = report.sections[-1].findings
    assert reassuring[0].code == "REASSURING_DPE_ADEME_VERIFIED"
    assert reassuring[0].title == "Enregistrement ADEME vérifié"
    assert reassuring[0].sources[0].page_number == number_source.page_number
    assert report.summary.reassuring_count == 2
