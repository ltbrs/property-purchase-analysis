"""Add missing-document metadata and persisted buyer reports.

Revision ID: 20260826_05
Revises: 20260826_04
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260826_05"
down_revision: str | Sequence[str] | None = "20260826_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "risk_findings", sa.Column("expectation_level", sa.String(length=30), nullable=True)
    )
    op.add_column("risk_findings", sa.Column("missing_reason", sa.String(length=20), nullable=True))
    op.drop_constraint("ck_risk_findings_category", "risk_findings", type_="check")
    op.create_check_constraint(
        "ck_risk_findings_category",
        "risk_findings",
        "category IN ('energy', 'coproperty', 'financial', 'diagnostics', 'consistency', "
        "'missing_information')",
    )
    op.create_check_constraint(
        "ck_risk_findings_expectation",
        "risk_findings",
        "expectation_level IS NULL OR expectation_level IN "
        "('definitely_expected', 'usually_useful', 'context_dependent')",
    )
    op.create_check_constraint(
        "ck_risk_findings_missing_reason",
        "risk_findings",
        "missing_reason IS NULL OR missing_reason IN ('absent', 'insufficient')",
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_case_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["analysis_case_id"], ["analysis_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_case_id"),
    )
    op.create_index("ix_reports_analysis_case_id", "reports", ["analysis_case_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_reports_analysis_case_id", table_name="reports")
    op.drop_table("reports")
    op.drop_constraint("ck_risk_findings_missing_reason", "risk_findings", type_="check")
    op.drop_constraint("ck_risk_findings_expectation", "risk_findings", type_="check")
    op.drop_constraint("ck_risk_findings_category", "risk_findings", type_="check")
    op.create_check_constraint(
        "ck_risk_findings_category",
        "risk_findings",
        "category IN ('energy', 'coproperty', 'financial', 'diagnostics', 'consistency')",
    )
    op.drop_column("risk_findings", "missing_reason")
    op.drop_column("risk_findings", "expectation_level")
