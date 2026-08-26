from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.documents.classification.models import DocumentType
from app.property.normalization.ag_minutes import (
    AgItemKind,
    AgItemStatus,
    NormalizedAgMinutes,
)
from app.property.normalization.dpe import NormalizedDpeFacts, SourceReference
from app.property.normalization.financials import (
    FinancialItemKind,
    NormalizedFinancials,
)
from app.risks.models import (
    DocumentExpectation,
    FindingStatus,
    MissingDocumentReason,
    RiskCategory,
    RiskFinding,
    RiskSeverity,
)


class AvailableDocument(BaseModel):
    document_id: UUID
    document_type: DocumentType
    document_date: date | None = None
    covered_period_end: date | None = None


class MissingDocumentContext(BaseModel):
    is_coproperty: bool | None = None


def _years_before(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def _unique_sources(sources: list[SourceReference]) -> list[SourceReference]:
    unique: list[SourceReference] = []
    seen: set[tuple[UUID, int]] = set()
    for source in sources:
        key = (source.document_id, source.page_number)
        if key not in seen:
            seen.add(key)
            unique.append(source)
    return unique


def _missing_finding(
    *,
    code: str,
    title: str,
    description: str,
    expectation: DocumentExpectation,
    reason: MissingDocumentReason,
    severity: RiskSeverity,
    sources: list[SourceReference] | None = None,
) -> RiskFinding:
    return RiskFinding(
        code=code,
        finding_key=code,
        category=RiskCategory.MISSING_INFORMATION,
        title=title,
        severity=severity,
        description=description,
        status=FindingStatus.MISSING_INFORMATION,
        sources=sources or [],
        expectation_level=expectation,
        missing_reason=reason,
    )


def evaluate_missing_documents(
    *,
    available_documents: list[AvailableDocument],
    dpe_documents: list[NormalizedDpeFacts],
    minutes: list[NormalizedAgMinutes],
    financials: list[NormalizedFinancials],
    as_of: date,
    context: MissingDocumentContext | None = None,
) -> list[RiskFinding]:
    """Identify absent or unusable buyer documents without making legal claims."""

    by_type: dict[DocumentType, list[AvailableDocument]] = {}
    for document in available_documents:
        by_type.setdefault(document.document_type, []).append(document)

    findings: list[RiskFinding] = []
    classified_dpe = by_type.get(DocumentType.DPE, [])
    has_usable_dpe = any(
        facts.dpe_rating.value is not None
        or facts.energy_consumption_kwh_m2_year.value is not None
        or facts.dpe_date.value is not None
        for facts in dpe_documents
    )
    if not classified_dpe and not dpe_documents:
        findings.append(
            _missing_finding(
                code="MISSING_DPE_DOCUMENT",
                title="DPE non fourni",
                description=(
                    "Aucun DPE n’a été identifié dans le dossier. Ce constat porte uniquement "
                    "sur les documents transmis."
                ),
                expectation=DocumentExpectation.DEFINITELY_EXPECTED,
                reason=MissingDocumentReason.ABSENT,
                severity=RiskSeverity.HIGH,
            )
        )
    elif not has_usable_dpe:
        findings.append(
            _missing_finding(
                code="INSUFFICIENT_DPE_DOCUMENT",
                title="DPE non exploitable",
                description=(
                    "Un document classé comme DPE est présent, mais aucune extraction structurée "
                    "validée n’est disponible."
                ),
                expectation=DocumentExpectation.DEFINITELY_EXPECTED,
                reason=MissingDocumentReason.INSUFFICIENT,
                severity=RiskSeverity.HIGH,
            )
        )

    coproperty_relevant = context is None or context.is_coproperty is not False
    classified_minutes = by_type.get(DocumentType.AG_MINUTES, [])
    meeting_dates = [document.meeting_date for document in minutes if document.meeting_date]
    meeting_dates.extend(
        document.document_date for document in classified_minutes if document.document_date
    )
    if coproperty_relevant and not classified_minutes and not minutes:
        findings.append(
            _missing_finding(
                code="MISSING_RECENT_AG_MINUTES",
                title="Procès-verbaux récents d’AG non fournis",
                description=(
                    "Aucun procès-verbal d’assemblée générale n’a été identifié. Ces documents "
                    "sont habituellement utiles pour comprendre les décisions et sujets en cours "
                    "d’une copropriété."
                ),
                expectation=DocumentExpectation.USUALLY_USEFUL,
                reason=MissingDocumentReason.ABSENT,
                severity=RiskSeverity.MEDIUM,
            )
        )
    elif coproperty_relevant and (
        not meeting_dates or max(meeting_dates) < _years_before(as_of, 3)
    ):
        findings.append(
            _missing_finding(
                code="INSUFFICIENT_RECENT_AG_MINUTES",
                title="Procès-verbaux d’AG trop anciens ou non datés",
                description=(
                    "Aucun procès-verbal daté de moins de trois ans n’a été retrouvé dans les "
                    "documents fournis."
                ),
                expectation=DocumentExpectation.USUALLY_USEFUL,
                reason=MissingDocumentReason.INSUFFICIENT,
                severity=RiskSeverity.MEDIUM,
            )
        )

    financial_types = {
        DocumentType.COPRO_FINANCIALS,
        DocumentType.CHARGES,
        DocumentType.WORKS_CALL,
    }
    classified_financials = [
        document for document in available_documents if document.document_type in financial_types
    ]
    has_financial_facts = any(document.items for document in financials)
    if coproperty_relevant and not classified_financials and not financials:
        findings.append(
            _missing_finding(
                code="MISSING_COPROPERTY_FINANCIALS",
                title="Informations financières de copropriété absentes",
                description=(
                    "Aucun relevé de charges, compte de copropriété ou appel de fonds n’a été "
                    "identifié. Ces éléments sont habituellement utiles pour apprécier les coûts."
                ),
                expectation=DocumentExpectation.USUALLY_USEFUL,
                reason=MissingDocumentReason.ABSENT,
                severity=RiskSeverity.MEDIUM,
            )
        )
    elif coproperty_relevant and not has_financial_facts:
        findings.append(
            _missing_finding(
                code="INSUFFICIENT_COPROPERTY_FINANCIALS",
                title="Informations financières non exploitables",
                description=(
                    "Des documents financiers ont été identifiés, mais aucune donnée structurée "
                    "validée n’est disponible."
                ),
                expectation=DocumentExpectation.USUALLY_USEFUL,
                reason=MissingDocumentReason.INSUFFICIENT,
                severity=RiskSeverity.MEDIUM,
            )
        )

    active_work_sources = [
        item.source
        for document in minutes
        for item in document.items
        if item.status not in {AgItemStatus.COMPLETED, AgItemStatus.REJECTED}
        and item.kind
        in {
            AgItemKind.WORKS,
            AgItemKind.FACADE,
            AgItemKind.ROOF,
            AgItemKind.ELEVATOR,
            AgItemKind.HEATING,
            AgItemKind.STRUCTURAL,
            AgItemKind.MAJOR_MAINTENANCE,
        }
    ]
    has_supporting_call = bool(by_type.get(DocumentType.WORKS_CALL)) or any(
        item.kind == FinancialItemKind.FUNDING_CALL
        for document in financials
        for item in document.items
    )
    if active_work_sources and not has_supporting_call:
        findings.append(
            _missing_finding(
                code="MISSING_WORKS_SUPPORTING_DOCUMENT",
                title="Justificatif financier des travaux non retrouvé",
                description=(
                    "Des travaux sont mentionnés, mais aucun appel de fonds ou justificatif "
                    "financier associé n’a été identifié dans le dossier."
                ),
                expectation=DocumentExpectation.CONTEXT_DEPENDENT,
                reason=MissingDocumentReason.ABSENT,
                severity=RiskSeverity.MEDIUM,
                sources=_unique_sources(active_work_sources),
            )
        )

    return findings
