"""Persist document processing and scanned page fallback

Revision ID: bbf1303e5070
Revises: 20260922_15
Create Date: 2026-09-28 13:44:18.760337
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "bbf1303e5070"
down_revision: str | Sequence[str] | None = "20260922_15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("processing_stage", sa.String(32)))
    op.add_column("documents", sa.Column("next_attempt_at", sa.DateTime(timezone=True)))
    op.add_column("documents", sa.Column("lease_until", sa.DateTime(timezone=True)))
    op.add_column("documents", sa.Column("lease_token", sa.Uuid()))
    op.add_column(
        "documents",
        sa.Column("processing_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column("processing_progress", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index(
        "ix_documents_processing_due",
        "documents",
        ["next_attempt_at", "lease_until"],
        postgresql_where=sa.text(
            "processing_stage IN ('queued', 'xberg', 'vision', 'classification', 'structured')"
        ),
    )
    op.create_index("ix_documents_processing_stage", "documents", ["processing_stage"])
    op.create_index("ix_documents_next_attempt_at", "documents", ["next_attempt_at"])
    op.add_column(
        "document_extraction_pages",
        sa.Column("extraction_method", sa.String(32), nullable=False, server_default="xberg"),
    )
    op.add_column(
        "document_extraction_pages",
        sa.Column("read_status", sa.String(32), nullable=False, server_default="read"),
    )
    op.add_column(
        "document_extraction_pages",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "document_extraction_pages", sa.Column("next_attempt_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "document_extraction_pages",
        sa.Column("vision_metadata", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "llm_rate_budgets",
        sa.Column("model", sa.String(100), primary_key=True),
        sa.Column("state", sa.JSON(), nullable=False),
    )
    # Internal server-owned state. Never expose admission history through the Data API.
    op.execute("ALTER TABLE public.llm_rate_budgets ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON public.llm_rate_budgets FROM anon, authenticated")
    # Recover work interrupted before persistent scheduling existed.
    op.execute(
        "UPDATE documents SET processing_stage = 'queued', next_attempt_at = now() "
        "WHERE status IN ('extracting', 'analyzing')"
    )


def downgrade() -> None:
    op.drop_table("llm_rate_budgets")
    for column in (
        "vision_metadata",
        "next_attempt_at",
        "attempts",
        "read_status",
        "extraction_method",
    ):
        op.drop_column("document_extraction_pages", column)
    op.drop_index("ix_documents_processing_due", table_name="documents")
    op.drop_index("ix_documents_processing_stage", table_name="documents")
    op.drop_index("ix_documents_next_attempt_at", table_name="documents")
    for column in (
        "processing_progress",
        "processing_attempts",
        "lease_token",
        "lease_until",
        "next_attempt_at",
        "processing_stage",
    ):
        op.drop_column("documents", column)
