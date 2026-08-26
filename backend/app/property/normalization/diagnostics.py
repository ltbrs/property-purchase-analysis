from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.property.normalization.common import (
    date_is_page_backed,
    normalize_iso_date,
    normalize_monetary_value,
    normalize_optional_text,
    page_contains_monetary_value,
    verified_source,
)
from app.property.normalization.dpe import SourceReference


class DiagnosticKind(StrEnum):
    ASBESTOS = "asbestos"
    LEAD = "lead"
    ELECTRICITY = "electricity"
    GAS = "gas"
    ENVIRONMENTAL_RISK = "environmental_risk"
    CARREZ = "carrez"


class DiagnosticResult(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    ANOMALY = "anomaly"
    RISK_IDENTIFIED = "risk_identified"
    CLEAR = "clear"
    UNKNOWN = "unknown"


class DiagnosticFindingCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: DiagnosticKind
    result: DiagnosticResult
    description: str
    diagnostic_date: str | None
    valid_until: str | None
    measured_surface_m2: str | None
    page_number: int
    quote: str = Field(max_length=300)


class DiagnosticExtractionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[DiagnosticFindingCandidate]


class NormalizedDiagnosticFinding(BaseModel):
    kind: DiagnosticKind
    result: DiagnosticResult
    description: str
    diagnostic_date: date | None
    valid_until: date | None
    measured_surface_m2: Decimal | None
    source: SourceReference


class NormalizedDiagnostics(BaseModel):
    findings: list[NormalizedDiagnosticFinding]


def normalize_diagnostics_candidate(
    candidate: DiagnosticExtractionCandidate,
    *,
    document_id: UUID,
    pages: dict[int, str],
) -> NormalizedDiagnostics:
    findings: list[NormalizedDiagnosticFinding] = []
    for item in candidate.findings:
        description = normalize_optional_text(item.description)
        source = verified_source(
            document_id=document_id,
            page_number=item.page_number,
            quote=item.quote,
            pages=pages,
        )
        if description is None or source is None or source.quote is None:
            continue
        diagnostic_date = normalize_iso_date(item.diagnostic_date)
        valid_until = normalize_iso_date(item.valid_until)
        if not date_is_page_backed(diagnostic_date, pages):
            diagnostic_date = None
        if not date_is_page_backed(valid_until, pages):
            valid_until = None
        if (
            diagnostic_date is not None
            and valid_until is not None
            and valid_until < diagnostic_date
        ):
            valid_until = None
        surface = normalize_monetary_value(item.measured_surface_m2)
        if not page_contains_monetary_value(surface, pages[item.page_number]):
            surface = None
        if surface is not None and not Decimal("0.1") <= surface <= Decimal("100000"):
            surface = None
        findings.append(
            NormalizedDiagnosticFinding(
                kind=item.kind,
                result=item.result,
                description=description,
                diagnostic_date=diagnostic_date,
                valid_until=valid_until,
                measured_surface_m2=surface,
                source=source,
            )
        )
    return NormalizedDiagnostics(findings=findings)
