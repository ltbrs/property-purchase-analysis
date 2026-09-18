from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.documents.repository import DocumentRepository
from app.property.models import AnalysisCaseRecord, PropertyType
from app.property.normalization.ag_minutes import NormalizedAgMinutes
from app.property.normalization.diagnostics import NormalizedDiagnostics
from app.property.normalization.dpe import NormalizedDpeFacts
from app.property.normalization.financials import NormalizedFinancials
from app.property.normalization.structured import StructuredExtractionType
from app.property.reconciliation import TimelineEvent
from app.reports import BuyerReport, build_buyer_report
from app.risks.engine import evaluate_case_risks
from app.risks.models import RiskFindingRead
from app.risks.rules.missing_documents import AvailableDocument, MissingDocumentContext


@dataclass(frozen=True)
class CaseAnalysisResult:
    findings: list[RiskFindingRead]
    timeline: list[TimelineEvent]
    dpe_documents: list[NormalizedDpeFacts]
    diagnostics: list[NormalizedDiagnostics]


class CaseAnalysisService:
    """Build and persist case findings and reports from normalized document data."""

    def __init__(self, repository: DocumentRepository) -> None:
        self.repository = repository

    def refresh_findings(
        self,
        *,
        analysis_case: AnalysisCaseRecord,
        user_id: UUID,
        as_of: date | None = None,
        demo_seed: bool = False,
    ) -> CaseAnalysisResult:
        dpe_documents = [
            NormalizedDpeFacts.model_validate(record.normalized_facts)
            for record in self.repository.list_case_dpe_extractions(
                analysis_case.id,
                user_id,
                include_unpublished_demo=demo_seed,
            )
        ]
        minutes: list[NormalizedAgMinutes] = []
        financials: list[NormalizedFinancials] = []
        diagnostics: list[NormalizedDiagnostics] = []
        for record in self.repository.list_case_structured_extractions(
            analysis_case.id,
            user_id,
            include_unpublished_demo=demo_seed,
        ):
            if record.extraction_type == StructuredExtractionType.AG_MINUTES.value:
                minutes.append(NormalizedAgMinutes.model_validate(record.normalized_facts))
            elif record.extraction_type == StructuredExtractionType.FINANCIALS.value:
                financials.append(NormalizedFinancials.model_validate(record.normalized_facts))
            elif record.extraction_type == StructuredExtractionType.DIAGNOSTICS.value:
                diagnostics.append(NormalizedDiagnostics.model_validate(record.normalized_facts))

        available_documents = [
            AvailableDocument.model_validate(
                {
                    "document_id": record.document_id,
                    "document_type": record.document_type,
                    "document_date": record.document_date,
                    "covered_period_end": record.covered_period_end,
                }
            )
            for record in self.repository.list_case_classifications(
                analysis_case.id,
                user_id,
                include_unpublished_demo=demo_seed,
            )
        ]
        missing_document_context = MissingDocumentContext(
            is_coproperty=(
                None
                if analysis_case.property_type == PropertyType.UNKNOWN.value
                else analysis_case.property_type == PropertyType.APARTMENT_COPROPERTY.value
            )
        )
        evaluation = evaluate_case_risks(
            dpe_documents=dpe_documents,
            minutes=minutes,
            financials=financials,
            diagnostics=diagnostics,
            available_documents=available_documents,
            missing_document_context=missing_document_context,
            as_of=as_of or date.today(),
        )
        records = self.repository.replace_case_findings(
            analysis_case_id=analysis_case.id,
            user_id=user_id,
            findings=evaluation.findings,
            allow_demo_seed=demo_seed,
        )
        return CaseAnalysisResult(
            findings=[RiskFindingRead.model_validate(record) for record in records],
            timeline=evaluation.reconciliation.timeline,
            dpe_documents=dpe_documents,
            diagnostics=diagnostics,
        )

    def refresh_report(
        self,
        *,
        analysis_case: AnalysisCaseRecord,
        user_id: UUID,
        as_of: date | None = None,
        demo_seed: bool = False,
    ) -> BuyerReport:
        analysis = self.refresh_findings(
            analysis_case=analysis_case,
            user_id=user_id,
            as_of=as_of,
            demo_seed=demo_seed,
        )
        documents = self.repository.list_documents(
            analysis_case.id,
            user_id,
            include_unpublished_demo=demo_seed,
        )
        report = build_buyer_report(
            analysis_case_id=analysis_case.id,
            title=analysis_case.title,
            findings=[
                record.to_finding()
                for record in (
                    self.repository.list_case_findings_for_demo_seed(analysis_case.id)
                    if demo_seed
                    else self.repository.list_case_findings(analysis_case.id, user_id)
                )
            ],
            document_names={document.id: document.original_filename for document in documents},
            dpe_documents=analysis.dpe_documents,
            diagnostics=analysis.diagnostics,
        )
        self.repository.save_case_report(
            analysis_case_id=analysis_case.id,
            user_id=user_id,
            report=report,
            allow_demo_seed=demo_seed,
        )
        return report
