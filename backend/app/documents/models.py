from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.property.models.analysis_case import PropertyType

if TYPE_CHECKING:
    from app.property.models import AnalysisCaseRecord


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentRecord(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("analysis_case_id", "sha256", name="uq_documents_case_sha256"),
        CheckConstraint("size_bytes > 0", name="ck_documents_size_positive"),
        CheckConstraint(
            "status IN ('uploaded', 'extracting', 'extracted', 'analyzing', 'completed', 'failed')",
            name="ck_documents_status_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    analysis_case_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("analysis_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default=DocumentStatus.UPLOADED.value,
        server_default=DocumentStatus.UPLOADED.value,
        nullable=False,
        index=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    analysis_case: Mapped["AnalysisCaseRecord"] = relationship(back_populates="documents")
    extraction: Mapped["DocumentExtractionRecord | None"] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )


class DocumentExtractionRecord(Base):
    __tablename__ = "document_extractions"
    __table_args__ = (
        CheckConstraint("duration_ms >= 0", name="ck_document_extractions_duration_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    parser_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parser_version: Mapped[str | None] = mapped_column(String(100))
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    document_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped[DocumentRecord] = relationship(back_populates="extraction")
    pages: Mapped[list["DocumentExtractionPageRecord"]] = relationship(
        back_populates="extraction",
        cascade="all, delete-orphan",
        order_by="DocumentExtractionPageRecord.page_number",
    )


class DocumentExtractionPageRecord(Base):
    __tablename__ = "document_extraction_pages"
    __table_args__ = (
        UniqueConstraint(
            "extraction_id", "page_number", name="uq_document_extraction_pages_number"
        ),
        CheckConstraint("page_number > 0", name="ck_document_extraction_pages_number_positive"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    extraction_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("document_extractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tables: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)

    extraction: Mapped[DocumentExtractionRecord] = relationship(back_populates="pages")


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_case_id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    failure_reason: str | None
    document_type: str | None = None
    created_at: datetime
    updated_at: datetime


class ExtractedTableRead(BaseModel):
    cells: list[list[str]] = Field(default_factory=list)
    markdown: str = ""
    table_id: str | None = None
    columns: list[str] | None = None
    bounding_box: dict[str, float] | None = None


class ExtractionPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_number: int
    text: str
    tables: list[ExtractedTableRead]


class DocumentExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    document_id: UUID
    parser_name: str
    parser_version: str | None
    duration_ms: int
    metadata: dict[str, object] = Field(validation_alias="document_metadata")
    pages: list[ExtractionPageRead]
    created_at: datetime


class AnalysisCaseCreate(BaseModel):
    title: str = Field(default="Mon achat immobilier", min_length=1, max_length=200)
    property_type: PropertyType = PropertyType.UNKNOWN

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("title must not be blank")
        return title


class AnalysisCaseUpdate(BaseModel):
    property_type: PropertyType


class AnalysisCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    property_type: PropertyType
    created_at: datetime
    updated_at: datetime
