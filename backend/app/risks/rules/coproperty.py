from collections import defaultdict
from decimal import Decimal

from app.property.normalization.ag_minutes import (
    AgItemKind,
    AgItemStatus,
    NormalizedAgItem,
    NormalizedAgMinutes,
)
from app.property.normalization.dpe import SourceReference
from app.risks.models import FindingStatus, RiskCategory, RiskFinding, RiskSeverity

MAJOR_WORK_KINDS = {
    AgItemKind.WORKS,
    AgItemKind.FACADE,
    AgItemKind.ROOF,
    AgItemKind.ELEVATOR,
    AgItemKind.HEATING,
    AgItemKind.STRUCTURAL,
    AgItemKind.MAJOR_MAINTENANCE,
}


def _unique_sources(items: list[NormalizedAgItem]) -> list[SourceReference]:
    seen: set[tuple[object, int]] = set()
    sources: list[SourceReference] = []
    for item in items:
        key = (item.source.document_id, item.source.page_number)
        if key not in seen:
            seen.add(key)
            sources.append(item.source)
    return sources


def evaluate_coproperty_risks(minutes: list[NormalizedAgMinutes]) -> list[RiskFinding]:
    items = [item for document in minutes for item in document.items]
    risks: list[RiskFinding] = []
    for item in items:
        source_key = f"{item.source.document_id}:{item.source.page_number}"
        if item.kind in MAJOR_WORK_KINDS and item.status == AgItemStatus.VOTED:
            severity = (
                RiskSeverity.CRITICAL if item.kind == AgItemKind.STRUCTURAL else RiskSeverity.HIGH
            )
            risks.append(
                RiskFinding(
                    code="COPRO_MAJOR_WORKS_VOTED",
                    finding_key=f"COPRO_MAJOR_WORKS_VOTED:{source_key}",
                    category=RiskCategory.COPROPERTY,
                    title="Travaux importants votés",
                    severity=severity,
                    description=item.description,
                    status=FindingStatus.CONFIRMED,
                    amount_eur=(
                        item.property_share_amount_eur
                        if item.property_share_amount_eur is not None
                        else item.amount_eur
                    ),
                    sources=[item.source],
                )
            )
        share = item.property_share_amount_eur
        if share is not None and share >= Decimal("5000"):
            risks.append(
                RiskFinding(
                    code="COPRO_HIGH_PROPERTY_SHARE_COST",
                    finding_key=f"COPRO_HIGH_PROPERTY_SHARE_COST:{source_key}",
                    category=RiskCategory.FINANCIAL,
                    title="Quote-part individuelle élevée",
                    severity=(
                        RiskSeverity.HIGH if share >= Decimal("10000") else RiskSeverity.MEDIUM
                    ),
                    description=f"Une quote-part explicite de {share} € est indiquée.",
                    status=FindingStatus.CONFIRMED,
                    amount_eur=share,
                    sources=[item.source],
                )
            )
        if (
            item.kind == AgItemKind.UNPAID_CHARGES
            and item.amount_eur is not None
            and item.amount_eur >= Decimal("5000")
        ):
            risks.append(
                RiskFinding(
                    code="COPRO_SIGNIFICANT_UNPAID_CHARGES",
                    finding_key=f"COPRO_SIGNIFICANT_UNPAID_CHARGES:{source_key}",
                    category=RiskCategory.FINANCIAL,
                    title="Impayés de copropriété signalés",
                    severity=(
                        RiskSeverity.HIGH
                        if item.amount_eur >= Decimal("10000")
                        else RiskSeverity.MEDIUM
                    ),
                    description=item.description,
                    status=FindingStatus.CONFIRMED,
                    amount_eur=item.amount_eur,
                    sources=[item.source],
                )
            )
        if item.kind == AgItemKind.LEGAL_DISPUTE and item.status != AgItemStatus.COMPLETED:
            risks.append(
                RiskFinding(
                    code="COPRO_LEGAL_DISPUTE",
                    finding_key=f"COPRO_LEGAL_DISPUTE:{source_key}",
                    category=RiskCategory.COPROPERTY,
                    title="Litige de copropriété",
                    severity=RiskSeverity.HIGH,
                    description=item.description,
                    status=FindingStatus.CONFIRMED,
                    sources=[item.source],
                )
            )

    by_kind: dict[AgItemKind, list[NormalizedAgItem]] = defaultdict(list)
    for item in items:
        by_kind[item.kind].append(item)
    for kind, related in by_kind.items():
        distinct_meetings = {item.meeting_date for item in related if item.meeting_date is not None}
        if len(distinct_meetings) < 2:
            continue
        if kind in MAJOR_WORK_KINDS and all(
            item.status in {AgItemStatus.DISCUSSED, AgItemStatus.PLANNED, AgItemStatus.UNKNOWN}
            for item in related
        ):
            risks.append(
                RiskFinding(
                    code="COPRO_MAJOR_WORKS_REPEATEDLY_DISCUSSED",
                    finding_key=f"COPRO_MAJOR_WORKS_REPEATEDLY_DISCUSSED:{kind.value}",
                    category=RiskCategory.COPROPERTY,
                    title="Travaux importants discutés à plusieurs reprises",
                    severity=RiskSeverity.MEDIUM,
                    description=(
                        f"Le sujet « {kind.value} » apparaît dans "
                        f"{len(distinct_meetings)} réunions "
                        "sans vote explicite extrait."
                    ),
                    status=FindingStatus.LIKELY,
                    confidence=0.8,
                    sources=_unique_sources(related),
                )
            )
        if kind == AgItemKind.WATER_INFILTRATION:
            risks.append(
                RiskFinding(
                    code="COPRO_RECURRING_WATER_INFILTRATION",
                    finding_key="COPRO_RECURRING_WATER_INFILTRATION",
                    category=RiskCategory.COPROPERTY,
                    title="Infiltrations d’eau récurrentes",
                    severity=RiskSeverity.HIGH,
                    description=(
                        "Des infiltrations sont mentionnées dans "
                        f"{len(distinct_meetings)} réunions."
                    ),
                    status=FindingStatus.LIKELY,
                    confidence=0.9,
                    sources=_unique_sources(related),
                )
            )
        if kind in {AgItemKind.FACADE, AgItemKind.ROOF}:
            unresolved = [
                item
                for item in related
                if item.status not in {AgItemStatus.COMPLETED, AgItemStatus.REJECTED}
            ]
            unresolved_meetings = {
                item.meeting_date for item in unresolved if item.meeting_date is not None
            }
            if len(unresolved_meetings) >= 2:
                risks.append(
                    RiskFinding(
                        code="COPRO_RECURRING_BUILDING_ENVELOPE_ISSUE",
                        finding_key=(f"COPRO_RECURRING_BUILDING_ENVELOPE_ISSUE:{kind.value}"),
                        category=RiskCategory.COPROPERTY,
                        title="Problème de façade ou toiture récurrent",
                        severity=RiskSeverity.HIGH,
                        description=(
                            f"Le sujet « {kind.value} » reste présent dans "
                            f"{len(unresolved_meetings)} réunions distinctes."
                        ),
                        status=FindingStatus.LIKELY,
                        confidence=0.85,
                        sources=_unique_sources(unresolved),
                    )
                )
    return risks
