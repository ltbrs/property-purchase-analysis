"""Persist structured document extractions and deterministic findings.

Revision ID: 20260826_04
Revises: 20260826_03
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260826_04"
down_revision: str | Sequence[str] | None = "20260826_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "structured_extractions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("extraction_type", sa.String(length=50), nullable=False),
        sa.Column("normalized_facts", sa.JSON(), nullable=False),
        sa.Column("requested_model", sa.String(length=100), nullable=False),
        sa.Column("resolved_model", sa.String(length=100), nullable=False),
        sa.Column("response_id", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "extraction_type IN ('ag_minutes', 'financials', 'diagnostics')",
            name="ck_structured_extractions_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id", "extraction_type", name="uq_structured_extractions_document_type"
        ),
    )
    op.create_index(
        "ix_structured_extractions_document_id", "structured_extractions", ["document_id"]
    )
    op.create_index(
        "ix_structured_extractions_extraction_type",
        "structured_extractions",
        ["extraction_type"],
    )

    op.create_table(
        "risk_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_case_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("finding_key", sa.String(length=300), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("amount_eur", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_risk_findings_confidence",
        ),
        sa.CheckConstraint(
            "amount_eur IS NULL OR amount_eur >= 0", name="ck_risk_amount_nonnegative"
        ),
        sa.CheckConstraint(
            "category IN ('energy', 'coproperty', 'financial', 'diagnostics', 'consistency')",
            name="ck_risk_findings_category",
        ),
        sa.CheckConstraint(
            "severity IN ('info', 'low', 'medium', 'high', 'critical')",
            name="ck_risk_findings_severity",
        ),
        sa.CheckConstraint(
            "status IN ('confirmed', 'likely', 'possible', 'missing_information')",
            name="ck_risk_findings_status",
        ),
        sa.ForeignKeyConstraint(["analysis_case_id"], ["analysis_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_case_id", "finding_key", name="uq_risk_findings_case_key"),
    )
    op.create_index("ix_risk_findings_analysis_case_id", "risk_findings", ["analysis_case_id"])
    op.create_index("ix_risk_findings_code", "risk_findings", ["code"])
    op.create_index("ix_risk_findings_category", "risk_findings", ["category"])
    op.create_index("ix_risk_findings_severity", "risk_findings", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_risk_findings_severity", table_name="risk_findings")
    op.drop_index("ix_risk_findings_category", table_name="risk_findings")
    op.drop_index("ix_risk_findings_code", table_name="risk_findings")
    op.drop_index("ix_risk_findings_analysis_case_id", table_name="risk_findings")
    op.drop_table("risk_findings")
    op.drop_index("ix_structured_extractions_extraction_type", table_name="structured_extractions")
    op.drop_index("ix_structured_extractions_document_id", table_name="structured_extractions")
    op.drop_table("structured_extractions")
