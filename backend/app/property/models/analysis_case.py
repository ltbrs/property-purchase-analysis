from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.documents.models import DocumentRecord


class PropertyType(StrEnum):
    UNKNOWN = "unknown"
    APARTMENT_COPROPERTY = "apartment_coproperty"
    HOUSE = "house"


class AnalysisCaseAccessMode(StrEnum):
    STANDARD = "standard"
    FREE_PREVIEW = "free_preview"
    GRANDFATHERED = "grandfathered"


class AnalysisCaseKind(StrEnum):
    USER = "user"
    DEMO = "demo"


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(254), index=True)
    email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    show_demo_case: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AuthAccountRecord(Base):
    __tablename__ = "auth_accounts"

    provider: Mapped[str] = mapped_column(String(50), primary_key=True)
    provider_account_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AnalysisCaseRecord(Base):
    __tablename__ = "analysis_cases"
    __table_args__ = (
        CheckConstraint(
            "property_type IN ('unknown', 'apartment_coproperty', 'house')",
            name="ck_analysis_cases_property_type",
        ),
        CheckConstraint(
            "price_eur IS NULL OR price_eur > 0",
            name="ck_analysis_cases_price_positive",
        ),
        CheckConstraint(
            "surface_m2 IS NULL OR surface_m2 > 0",
            name="ck_analysis_cases_surface_positive",
        ),
        CheckConstraint(
            "lot_count IS NULL OR lot_count > 0",
            name="ck_analysis_cases_lot_count_positive",
        ),
        CheckConstraint(
            "access_mode IN ('standard', 'free_preview', 'grandfathered')",
            name="ck_analysis_cases_access_mode",
        ),
        CheckConstraint(
            "case_kind IN ('user', 'demo')",
            name="ck_analysis_cases_case_kind",
        ),
        CheckConstraint(
            "(case_kind = 'user' AND user_id IS NOT NULL "
            "AND template_key IS NULL AND template_manifest_sha256 IS NULL "
            "AND published_at IS NULL) OR "
            "(case_kind = 'demo' AND user_id IS NULL "
            "AND template_key IS NOT NULL AND template_manifest_sha256 IS NOT NULL "
            "AND access_mode = 'grandfathered')",
            name="ck_analysis_cases_kind_fields",
        ),
        CheckConstraint(
            "template_manifest_sha256 IS NULL OR length(template_manifest_sha256) = 64",
            name="ck_analysis_cases_template_manifest_sha256_length",
        ),
        Index(
            "uq_analysis_cases_one_free_preview_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("access_mode = 'free_preview' AND case_kind = 'user'"),
            sqlite_where=text("access_mode = 'free_preview' AND case_kind = 'user'"),
        ),
        Index(
            "uq_analysis_cases_demo_template_key",
            "template_key",
            unique=True,
            postgresql_where=text("case_kind = 'demo'"),
            sqlite_where=text("case_kind = 'demo'"),
        ),
        Index(
            "uq_analysis_cases_one_published_demo",
            "case_kind",
            unique=True,
            postgresql_where=text("case_kind = 'demo' AND published_at IS NOT NULL"),
            sqlite_where=text("case_kind = 'demo' AND published_at IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    property_type: Mapped[str] = mapped_column(
        String(30),
        default=PropertyType.UNKNOWN.value,
        server_default=PropertyType.UNKNOWN.value,
        nullable=False,
    )
    price_eur: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    surface_m2: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    lot_count: Mapped[int | None] = mapped_column(Integer)
    access_mode: Mapped[str] = mapped_column(
        String(30),
        default=AnalysisCaseAccessMode.STANDARD.value,
        server_default=AnalysisCaseAccessMode.STANDARD.value,
        nullable=False,
    )
    case_kind: Mapped[str] = mapped_column(
        String(20),
        default=AnalysisCaseKind.USER.value,
        server_default=AnalysisCaseKind.USER.value,
        nullable=False,
    )
    template_key: Mapped[str | None] = mapped_column(String(100))
    template_manifest_sha256: Mapped[str | None] = mapped_column(String(64))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    documents: Mapped[list["DocumentRecord"]] = relationship(
        back_populates="analysis_case", cascade="all, delete-orphan"
    )
