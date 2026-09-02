from datetime import datetime

from sqlalchemy.orm import Session

from app.contact.models import (
    ContactSubmissionCreate,
    ContactSubmissionRecord,
)


class ContactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_submission(
        self,
        payload: ContactSubmissionCreate,
        *,
        ip_hash: str,
        now: datetime,
    ) -> ContactSubmissionRecord:
        submission = ContactSubmissionRecord(
            name=payload.name,
            email=payload.email,
            subject=payload.subject.value,
            message=payload.message,
            ip_hash=ip_hash,
            privacy_consent_at=now,
        )
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(submission)
        return submission
