from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StructuredExtractionType(StrEnum):
    AG_MINUTES = "ag_minutes"
    FINANCIALS = "financials"
    DIAGNOSTICS = "diagnostics"


class StructuredExtractionRecord(Base):
    __tablename__ = "structured_extractions"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "extraction_type", name="uq_structured_extractions_document_type"
        ),
        CheckConstraint(
            "extraction_type IN ('ag_minutes', 'financials', 'diagnostics')",
            name="ck_structured_extractions_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    extraction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    normalized_facts: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    requested_model: Mapped[str] = mapped_column(String(100), nullable=False)
    resolved_model: Mapped[str] = mapped_column(String(100), nullable=False)
    response_id: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StructuredExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    extraction_type: StructuredExtractionType
    normalized_facts: dict[str, object]
    requested_model: str
    resolved_model: str
    prompt_version: str
    created_at: datetime
