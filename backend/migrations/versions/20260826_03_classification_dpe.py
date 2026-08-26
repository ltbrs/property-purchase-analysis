"""Persist document classifications and normalized DPE facts.

Revision ID: 20260826_03
Revises: 20260826_02
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260826_03"
down_revision: str | Sequence[str] | None = "20260826_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_classifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("covered_period_start", sa.Date(), nullable=True),
        sa.Column("covered_period_end", sa.Date(), nullable=True),
        sa.Column("issuer", sa.String(length=500), nullable=True),
        sa.Column("extraction_strategy", sa.String(length=50), nullable=True),
        sa.Column("requested_model", sa.String(length=100), nullable=False),
        sa.Column("resolved_model", sa.String(length=100), nullable=False),
        sa.Column("response_id", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("raw_output", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_classification_confidence",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(
        "ix_document_classifications_document_id",
        "document_classifications",
        ["document_id"],
    )
    op.create_index(
        "ix_document_classifications_document_type",
        "document_classifications",
        ["document_type"],
    )
    op.create_table(
        "dpe_extractions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("normalized_facts", sa.JSON(), nullable=False),
        sa.Column("requested_model", sa.String(length=100), nullable=False),
        sa.Column("resolved_model", sa.String(length=100), nullable=False),
        sa.Column("response_id", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index("ix_dpe_extractions_document_id", "dpe_extractions", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_dpe_extractions_document_id", table_name="dpe_extractions")
    op.drop_table("dpe_extractions")
    op.drop_index(
        "ix_document_classifications_document_type",
        table_name="document_classifications",
    )
    op.drop_index(
        "ix_document_classifications_document_id",
        table_name="document_classifications",
    )
    op.drop_table("document_classifications")
