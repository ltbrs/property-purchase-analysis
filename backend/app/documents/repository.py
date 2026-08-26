from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.documents.models import DocumentRecord
from app.property.models import AnalysisCaseRecord, UserRecord


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

    def create_analysis_case(self, user_id: UUID, title: str) -> AnalysisCaseRecord:
        self.ensure_user(user_id)
        analysis_case = AnalysisCaseRecord(user_id=user_id, title=title)
        self.session.add(analysis_case)
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
