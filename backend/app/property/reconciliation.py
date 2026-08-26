from collections import defaultdict
from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel

from app.property.normalization.ag_minutes import (
    AgItemStatus,
    NormalizedAgItem,
    NormalizedAgMinutes,
)
from app.property.normalization.common import searchable
from app.property.normalization.diagnostics import (
    DiagnosticKind,
    NormalizedDiagnostics,
)
from app.property.normalization.dpe import NormalizedDpeFacts, SourceReference
from app.property.normalization.financials import (
    FinancialItemKind,
    NormalizedFinancialItem,
    NormalizedFinancials,
)
from app.risks.models import FindingStatus, RiskCategory, RiskFinding, RiskSeverity


class TimelineEventType(StrEnum):
    AG_ITEM = "ag_item"
    FINANCIAL_ITEM = "financial_item"


class TimelineEvent(BaseModel):
    event_date: date
    event_type: TimelineEventType
    subject: str
    status: str
    amount_eur: Decimal | None
    source: SourceReference


class ReconciliationResult(BaseModel):
    timeline: list[TimelineEvent]
    findings: list[RiskFinding]


def build_timeline(
    minutes: list[NormalizedAgMinutes], financials: list[NormalizedFinancials]
) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for ag_item in (entry for document in minutes for entry in document.items):
        if ag_item.meeting_date is not None:
            events.append(
                TimelineEvent(
                    event_date=ag_item.meeting_date,
                    event_type=TimelineEventType.AG_ITEM,
                    subject=ag_item.description,
                    status=ag_item.status.value,
                    amount_eur=(
                        ag_item.property_share_amount_eur
                        if ag_item.property_share_amount_eur is not None
                        else ag_item.amount_eur
                    ),
                    source=ag_item.source,
                )
            )
    for financial_item in (entry for document in financials for entry in document.items):
        event_date = financial_item.due_date or financial_item.period_end
        if event_date is not None:
            events.append(
                TimelineEvent(
                    event_date=event_date,
                    event_type=TimelineEventType.FINANCIAL_ITEM,
                    subject=financial_item.related_project or financial_item.description,
                    status=financial_item.kind.value,
                    amount_eur=(
                        financial_item.property_share_amount_eur
                        if financial_item.property_share_amount_eur is not None
                        else financial_item.amount_eur
                    ),
                    source=financial_item.source,
                )
            )
    return sorted(events, key=lambda event: (event.event_date, event.event_type.value))


def _source_key(source: SourceReference) -> str:
    return f"{source.document_id}:{source.page_number}"


def _subject_matches(work: NormalizedAgItem, financial: NormalizedFinancialItem) -> bool:
    project = financial.related_project or financial.description
    left = set(searchable(work.description).split())
    right = set(searchable(project).split())
    meaningful = {word for word in left if len(word) >= 5}
    return bool(meaningful & right)


def reconcile_case(
    *,
    dpe_documents: list[NormalizedDpeFacts],
    minutes: list[NormalizedAgMinutes],
    financials: list[NormalizedFinancials],
    diagnostics: list[NormalizedDiagnostics],
) -> ReconciliationResult:
    findings: list[RiskFinding] = []

    heating = [
        facts.heating_type
        for facts in dpe_documents
        if facts.heating_type.value is not None and facts.heating_type.source is not None
    ]
    heating_values = {searchable(fact.value or "") for fact in heating}
    if len(heating_values) > 1:
        findings.append(
            RiskFinding(
                code="INCONSISTENT_HEATING_TYPE",
                finding_key="INCONSISTENT_HEATING_TYPE",
                category=RiskCategory.CONSISTENCY,
                title="Types de chauffage contradictoires",
                severity=RiskSeverity.MEDIUM,
                description="Plusieurs documents donnent des types de chauffage différents.",
                status=FindingStatus.POSSIBLE,
                confidence=0.9,
                sources=[fact.source for fact in heating if fact.source is not None],
            )
        )

    surfaces: list[tuple[str, Decimal, SourceReference]] = []
    for facts in dpe_documents:
        if facts.surface.value is not None and facts.surface.source is not None:
            surfaces.append(("DPE", Decimal(str(facts.surface.value)), facts.surface.source))
    for diagnostic in (finding for document in diagnostics for finding in document.findings):
        if diagnostic.kind == DiagnosticKind.CARREZ and diagnostic.measured_surface_m2 is not None:
            surfaces.append(("Carrez", diagnostic.measured_surface_m2, diagnostic.source))
    for index, left in enumerate(surfaces):
        for right in surfaces[index + 1 :]:
            difference = abs(left[1] - right[1])
            baseline = min(left[1], right[1])
            if difference <= Decimal("1") or difference / baseline <= Decimal("0.02"):
                continue
            key = ":".join(sorted((_source_key(left[2]), _source_key(right[2]))))
            findings.append(
                RiskFinding(
                    code="INCONSISTENT_PROPERTY_SURFACE",
                    finding_key=f"INCONSISTENT_PROPERTY_SURFACE:{key}",
                    category=RiskCategory.CONSISTENCY,
                    title="Surfaces documentaires différentes",
                    severity=RiskSeverity.MEDIUM,
                    description=(
                        f"La surface {left[0]} ({left[1]} m²) diffère de la surface "
                        f"{right[0]} ({right[1]} m²). Ces mesures peuvent avoir des "
                        "périmètres différents."
                    ),
                    status=FindingStatus.POSSIBLE,
                    confidence=0.95,
                    sources=[left[2], right[2]],
                )
            )

    ag_items = [item for document in minutes for item in document.items]
    financial_items = [item for document in financials for item in document.items]
    calls = [item for item in financial_items if item.kind == FinancialItemKind.FUNDING_CALL]
    for work in (item for item in ag_items if item.status == AgItemStatus.VOTED):
        later_calls = [
            call
            for call in calls
            if (
                work.meeting_date is None
                or call.due_date is None
                or call.due_date >= work.meeting_date
            )
            and _subject_matches(work, call)
        ]
        if not later_calls:
            findings.append(
                RiskFinding(
                    code="VOTED_WORK_WITHOUT_MATCHING_FUNDING_CALL",
                    finding_key=f"VOTED_WORK_WITHOUT_MATCHING_FUNDING_CALL:{_source_key(work.source)}",
                    category=RiskCategory.CONSISTENCY,
                    title="Appel de fonds non rapproché des travaux votés",
                    severity=RiskSeverity.MEDIUM,
                    description=(
                        "Des travaux sont indiqués comme votés, mais aucun appel de fonds nommé "
                        "correspondant n’a été rapproché dans les documents fournis."
                    ),
                    status=FindingStatus.MISSING_INFORMATION,
                    sources=[work.source],
                )
            )

    meeting_dates = sorted(
        {document.meeting_date for document in minutes if document.meeting_date is not None}
    )
    if meeting_dates:
        latest = meeting_dates[-1]
        for ag_item in ag_items:
            if (
                ag_item.meeting_date is None
                or ag_item.meeting_date >= latest
                or ag_item.status not in {AgItemStatus.DISCUSSED, AgItemStatus.PLANNED}
            ):
                continue
            if not any(
                later.kind == ag_item.kind
                and later.meeting_date is not None
                and later.meeting_date > ag_item.meeting_date
                for later in ag_items
            ):
                findings.append(
                    RiskFinding(
                        code="AG_PROJECT_NOT_FOLLOWED_UP",
                        finding_key=f"AG_PROJECT_NOT_FOLLOWED_UP:{_source_key(ag_item.source)}",
                        category=RiskCategory.CONSISTENCY,
                        title="Projet sans suivi retrouvé dans les AG suivantes",
                        severity=RiskSeverity.LOW,
                        description=(
                            "Un sujet discuté ou planifié n’apparaît plus dans les procès-verbaux "
                            "ultérieurs fournis; son issue reste à vérifier."
                        ),
                        status=FindingStatus.MISSING_INFORMATION,
                        sources=[ag_item.source],
                    )
                )

    annual_by_period: dict[date, list[NormalizedFinancialItem]] = defaultdict(list)
    for financial_item in financial_items:
        if (
            financial_item.kind == FinancialItemKind.ANNUAL_CHARGES
            and financial_item.period_end is not None
            and financial_item.amount_eur is not None
        ):
            annual_by_period[financial_item.period_end].append(financial_item)
    for period_end, values in annual_by_period.items():
        amounts = {item.amount_eur for item in values}
        if len(amounts) > 1:
            findings.append(
                RiskFinding(
                    code="INCONSISTENT_ANNUAL_CHARGES",
                    finding_key=f"INCONSISTENT_ANNUAL_CHARGES:{period_end}",
                    category=RiskCategory.CONSISTENCY,
                    title="Montants annuels de charges contradictoires",
                    severity=RiskSeverity.MEDIUM,
                    description=(
                        f"Plusieurs montants de charges sont associés à la période finissant le "
                        f"{period_end.isoformat()}."
                    ),
                    status=FindingStatus.POSSIBLE,
                    confidence=0.95,
                    sources=[item.source for item in values],
                )
            )

    return ReconciliationResult(
        timeline=build_timeline(minutes, financials),
        findings=findings,
    )
