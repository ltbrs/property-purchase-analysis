from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import case, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.documents.classification.models import (
    DocumentClassificationCandidate,
    DocumentClassificationRecord,
    DocumentType,
    ExtractionStrategy,
)
from app.documents.models import (
    DocumentExtractionPageRecord,
    DocumentExtractionRecord,
    DocumentRecord,
    DocumentStatus,
)
from app.documents.parsers.base import ParsedPdf
from app.property.models import AnalysisCaseRecord, PropertyType, UserRecord
from app.property.normalization.dpe import (
    DpeExtractionRecord,
    NormalizedDpeFacts,
)
from app.property.normalization.structured import (
    StructuredExtractionRecord,
    StructuredExtractionType,
)
from app.reports.models import BuyerReport, ReportRecord
from app.risks.models.findings import RiskFinding, RiskFindingRecord


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_user(self, user_id: UUID) -> None:
        if self.session.get(UserRecord, user_id) is None:
            self.session.add(UserRecord(id=user_id))
            try:
                self.session.flush()
            except IntegrityError:
                # Two first requests for one upstream identity may race. The
                # identity already exists, so only the losing transaction rolls back.
                self.session.rollback()

    def create_analysis_case(
        self,
        user_id: UUID,
        title: str,
        property_type: PropertyType = PropertyType.UNKNOWN,
    ) -> AnalysisCaseRecord:
        self.ensure_user(user_id)
        analysis_case = AnalysisCaseRecord(
            user_id=user_id,
            title=title,
            property_type=property_type.value,
        )
        self.session.add(analysis_case)
        self.session.commit()
        self.session.refresh(analysis_case)
        return analysis_case

    def update_analysis_case_property_type(
        self,
        analysis_case: AnalysisCaseRecord,
        property_type: PropertyType,
    ) -> AnalysisCaseRecord:
        analysis_case.property_type = property_type.value
        self.session.execute(
            delete(RiskFindingRecord).where(
                RiskFindingRecord.analysis_case_id == analysis_case.id
            )
        )
        self.session.execute(
            delete(ReportRecord).where(ReportRecord.analysis_case_id == analysis_case.id)
        )
        self.session.commit()
        self.session.refresh(analysis_case)
        return analysis_case

    def get_owned_analysis_case(
        self, analysis_case_id: UUID, user_id: UUID
    ) -> AnalysisCaseRecord | None:
        return self.session.scalar(
            select(AnalysisCaseRecord).where(
                AnalysisCaseRecord.id == analysis_case_id,
                AnalysisCaseRecord.user_id == user_id,
            )
        )

    def list_documents(self, analysis_case_id: UUID, user_id: UUID) -> list[DocumentRecord]:
        return list(
            self.session.scalars(
                select(DocumentRecord)
                .join(DocumentRecord.analysis_case)
                .where(
                    DocumentRecord.analysis_case_id == analysis_case_id,
                    AnalysisCaseRecord.user_id == user_id,
                )
                .order_by(DocumentRecord.created_at.desc())
            )
        )

    def find_by_checksum(
        self, analysis_case_id: UUID, user_id: UUID, sha256: str
    ) -> DocumentRecord | None:
        return self.session.scalar(
            select(DocumentRecord)
            .join(DocumentRecord.analysis_case)
            .where(
                DocumentRecord.analysis_case_id == analysis_case_id,
                AnalysisCaseRecord.user_id == user_id,
                DocumentRecord.sha256 == sha256,
            )
        )

    def get_owned_document(
        self, analysis_case_id: UUID, document_id: UUID, user_id: UUID
    ) -> DocumentRecord | None:
        return self.session.scalar(
            select(DocumentRecord)
            .join(DocumentRecord.analysis_case)
            .where(
                DocumentRecord.id == document_id,
                DocumentRecord.analysis_case_id == analysis_case_id,
                AnalysisCaseRecord.user_id == user_id,
            )
        )

    def get_extraction(self, document_id: UUID) -> DocumentExtractionRecord | None:
        return self.session.scalar(
            select(DocumentExtractionRecord)
            .options(selectinload(DocumentExtractionRecord.pages))
            .where(DocumentExtractionRecord.document_id == document_id)
        )

    def get_classification(self, document_id: UUID) -> DocumentClassificationRecord | None:
        return self.session.scalar(
            select(DocumentClassificationRecord).where(
                DocumentClassificationRecord.document_id == document_id
            )
        )

    def list_case_classifications(
        self, analysis_case_id: UUID, user_id: UUID
    ) -> list[DocumentClassificationRecord]:
        return list(
            self.session.scalars(
                select(DocumentClassificationRecord)
                .join(DocumentRecord, DocumentRecord.id == DocumentClassificationRecord.document_id)
                .join(DocumentRecord.analysis_case)
                .where(
                    DocumentRecord.analysis_case_id == analysis_case_id,
                    AnalysisCaseRecord.user_id == user_id,
                )
                .order_by(DocumentClassificationRecord.created_at)
            )
        )

    def get_dpe_extraction(self, document_id: UUID) -> DpeExtractionRecord | None:
        return self.session.scalar(
            select(DpeExtractionRecord).where(DpeExtractionRecord.document_id == document_id)
        )

    def get_structured_extraction(
        self, document_id: UUID, extraction_type: StructuredExtractionType
    ) -> StructuredExtractionRecord | None:
        return self.session.scalar(
            select(StructuredExtractionRecord).where(
                StructuredExtractionRecord.document_id == document_id,
                StructuredExtractionRecord.extraction_type == extraction_type.value,
            )
        )

    def list_case_dpe_extractions(
        self, analysis_case_id: UUID, user_id: UUID
    ) -> list[DpeExtractionRecord]:
        return list(
            self.session.scalars(
                select(DpeExtractionRecord)
                .join(DocumentRecord, DocumentRecord.id == DpeExtractionRecord.document_id)
                .join(DocumentRecord.analysis_case)
                .where(
                    DocumentRecord.analysis_case_id == analysis_case_id,
                    AnalysisCaseRecord.user_id == user_id,
                )
            )
        )

    def list_case_structured_extractions(
        self, analysis_case_id: UUID, user_id: UUID
    ) -> list[StructuredExtractionRecord]:
        return list(
            self.session.scalars(
                select(StructuredExtractionRecord)
                .join(DocumentRecord, DocumentRecord.id == StructuredExtractionRecord.document_id)
                .join(DocumentRecord.analysis_case)
                .where(
                    DocumentRecord.analysis_case_id == analysis_case_id,
                    AnalysisCaseRecord.user_id == user_id,
                )
                .order_by(StructuredExtractionRecord.created_at)
            )
        )

    def mark_extracting(self, document: DocumentRecord) -> None:
        document.status = DocumentStatus.EXTRACTING.value
        document.failure_reason = None
        self.session.commit()

    def mark_extraction_failed(self, document: DocumentRecord, failure_reason: str) -> None:
        document.status = DocumentStatus.FAILED.value
        document.failure_reason = failure_reason[:500]
        self.session.commit()

    def mark_analyzing(self, document: DocumentRecord) -> None:
        document.status = DocumentStatus.ANALYZING.value
        document.failure_reason = None
        self.session.commit()

    def mark_analysis_failed(self, document: DocumentRecord, failure_reason: str) -> None:
        document.status = DocumentStatus.FAILED.value
        document.failure_reason = failure_reason[:500]
        self.session.commit()

    def save_extraction(
        self,
        document: DocumentRecord,
        parsed: ParsedPdf,
        parser_name: str,
        parser_version: str | None,
        duration_ms: int,
    ) -> DocumentExtractionRecord:
        extraction = DocumentExtractionRecord(
            document_id=document.id,
            parser_name=parser_name,
            parser_version=parser_version,
            duration_ms=duration_ms,
            document_metadata=parsed.metadata,
            pages=[
                DocumentExtractionPageRecord(
                    page_number=page.page_number,
                    text=page.text,
                    tables=[table.model_dump(mode="json") for table in page.tables],
                )
                for page in parsed.pages
            ],
        )
        self.session.add(extraction)
        document.status = DocumentStatus.EXTRACTED.value
        document.failure_reason = None
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.session.refresh(extraction)
        self.session.refresh(extraction, attribute_names=["pages"])
        return extraction

    def save_classification(
        self,
        *,
        document: DocumentRecord,
        candidate: DocumentClassificationCandidate,
        normalized_document_type: DocumentType,
        normalized_strategy: ExtractionStrategy | None,
        requested_model: str,
        resolved_model: str,
        response_id: str,
        prompt_version: str,
    ) -> DocumentClassificationRecord:
        classification = DocumentClassificationRecord(
            document_id=document.id,
            document_type=normalized_document_type.value,
            confidence=candidate.confidence,
            document_date=candidate.document_date,
            covered_period_start=candidate.covered_period_start,
            covered_period_end=candidate.covered_period_end,
            issuer=candidate.issuer,
            extraction_strategy=(normalized_strategy.value if normalized_strategy else None),
            requested_model=requested_model,
            resolved_model=resolved_model,
            response_id=response_id,
            prompt_version=prompt_version,
            raw_output=candidate.model_dump(mode="json"),
        )
        self.session.add(classification)
        document.status = DocumentStatus.EXTRACTED.value
        document.failure_reason = None
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.session.refresh(classification)
        return classification

    def save_dpe_extraction(
        self,
        *,
        document: DocumentRecord,
        facts: NormalizedDpeFacts,
        requested_model: str,
        resolved_model: str,
        response_id: str,
        prompt_version: str,
    ) -> DpeExtractionRecord:
        dpe_extraction = DpeExtractionRecord(
            document_id=document.id,
            normalized_facts=facts.model_dump(mode="json"),
            requested_model=requested_model,
            resolved_model=resolved_model,
            response_id=response_id,
            prompt_version=prompt_version,
        )
        self.session.add(dpe_extraction)
        document.status = DocumentStatus.COMPLETED.value
        document.failure_reason = None
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.session.refresh(dpe_extraction)
        return dpe_extraction

    def save_structured_extraction(
        self,
        *,
        document: DocumentRecord,
        extraction_type: StructuredExtractionType,
        normalized_facts: BaseModel,
        requested_model: str,
        resolved_model: str,
        response_id: str,
        prompt_version: str,
    ) -> StructuredExtractionRecord:
        extraction = StructuredExtractionRecord(
            document_id=document.id,
            extraction_type=extraction_type.value,
            normalized_facts=normalized_facts.model_dump(mode="json"),
            requested_model=requested_model,
            resolved_model=resolved_model,
            response_id=response_id,
            prompt_version=prompt_version,
        )
        self.session.add(extraction)
        document.status = DocumentStatus.COMPLETED.value
        document.failure_reason = None
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.session.refresh(extraction)
        return extraction

    def replace_case_findings(
        self,
        *,
        analysis_case_id: UUID,
        user_id: UUID,
        findings: list[RiskFinding],
    ) -> list[RiskFindingRecord]:
        if self.get_owned_analysis_case(analysis_case_id, user_id) is None:
            raise PermissionError("Analysis case is not owned by the current user")
        existing = list(
            self.session.scalars(
                select(RiskFindingRecord).where(
                    RiskFindingRecord.analysis_case_id == analysis_case_id
                )
            )
        )
        for record in existing:
            self.session.delete(record)
        # Flush removals before inserting identical deterministic keys on refresh.
        self.session.flush()
        records = [
            RiskFindingRecord.from_finding(analysis_case_id=analysis_case_id, finding=finding)
            for finding in findings
        ]
        self.session.add_all(records)
        self.session.commit()
        for record in records:
            self.session.refresh(record)
        return records

    def list_case_findings(self, analysis_case_id: UUID, user_id: UUID) -> list[RiskFindingRecord]:
        if self.get_owned_analysis_case(analysis_case_id, user_id) is None:
            return []
        return list(
            self.session.scalars(
                select(RiskFindingRecord)
                .where(RiskFindingRecord.analysis_case_id == analysis_case_id)
                .order_by(
                    case(
                        (RiskFindingRecord.severity == "critical", 5),
                        (RiskFindingRecord.severity == "high", 4),
                        (RiskFindingRecord.severity == "medium", 3),
                        (RiskFindingRecord.severity == "low", 2),
                        else_=1,
                    ).desc(),
                    RiskFindingRecord.code,
                    RiskFindingRecord.finding_key,
                )
            )
        )

    def save_case_report(
        self, *, analysis_case_id: UUID, user_id: UUID, report: BuyerReport
    ) -> ReportRecord:
        if self.get_owned_analysis_case(analysis_case_id, user_id) is None:
            raise PermissionError("Analysis case is not owned by the current user")
        record = self.session.scalar(
            select(ReportRecord).where(ReportRecord.analysis_case_id == analysis_case_id)
        )
        if record is None:
            record = ReportRecord.from_report(report)
            self.session.add(record)
        else:
            record.update_from_report(report)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_case_report(self, analysis_case_id: UUID, user_id: UUID) -> ReportRecord | None:
        if self.get_owned_analysis_case(analysis_case_id, user_id) is None:
            return None
        return self.session.scalar(
            select(ReportRecord).where(ReportRecord.analysis_case_id == analysis_case_id)
        )

    def create_document(self, document: DocumentRecord, user_id: UUID) -> DocumentRecord:
        if self.get_owned_analysis_case(document.analysis_case_id, user_id) is None:
            raise PermissionError("Analysis case is not owned by the current user")

        self.session.add(document)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.find_by_checksum(document.analysis_case_id, user_id, document.sha256)
            if existing is None:
                raise
            return existing

        self.session.refresh(document)
        return document

    def delete_document(self, document: DocumentRecord) -> None:
        """Delete a document and invalidate case-level results derived from it."""
        self.session.execute(
            delete(DocumentClassificationRecord).where(
                DocumentClassificationRecord.document_id == document.id
            )
        )
        self.session.execute(
            delete(DpeExtractionRecord).where(DpeExtractionRecord.document_id == document.id)
        )
        self.session.execute(
            delete(StructuredExtractionRecord).where(
                StructuredExtractionRecord.document_id == document.id
            )
        )
        self.session.execute(
            delete(RiskFindingRecord).where(
                RiskFindingRecord.analysis_case_id == document.analysis_case_id
            )
        )
        self.session.execute(
            delete(ReportRecord).where(ReportRecord.analysis_case_id == document.analysis_case_id)
        )
        self.session.delete(document)
        self.session.commit()
