"""Persist page-level PDF extraction output.

Revision ID: 20260826_02
Revises: 20260826_01
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260826_02"
down_revision: str | Sequence[str] | None = "20260826_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_extractions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("parser_name", sa.String(length=100), nullable=False),
        sa.Column("parser_version", sa.String(length=100), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("duration_ms >= 0", name="ck_document_extractions_duration_nonnegative"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index("ix_document_extractions_document_id", "document_extractions", ["document_id"])
    op.create_table(
        "document_extraction_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("extraction_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("tables", sa.JSON(), nullable=False),
        sa.CheckConstraint("page_number > 0", name="ck_document_extraction_pages_number_positive"),
        sa.ForeignKeyConstraint(["extraction_id"], ["document_extractions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "extraction_id", "page_number", name="uq_document_extraction_pages_number"
        ),
    )
    op.create_index(
        "ix_document_extraction_pages_extraction_id",
        "document_extraction_pages",
        ["extraction_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_extraction_pages_extraction_id",
        table_name="document_extraction_pages",
    )
    op.drop_table("document_extraction_pages")
    op.drop_index("ix_document_extractions_document_id", table_name="document_extractions")
    op.drop_table("document_extractions")
