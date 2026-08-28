from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.documents.models import DocumentRecord


class PropertyType(StrEnum):
    UNKNOWN = "unknown"
    APARTMENT_COPROPERTY = "apartment_coproperty"
    HOUSE = "house"


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
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
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    documents: Mapped[list["DocumentRecord"]] = relationship(
        back_populates="analysis_case", cascade="all, delete-orphan"
    )
