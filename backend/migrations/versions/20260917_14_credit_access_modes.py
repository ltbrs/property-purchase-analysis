"""Add free preview and grandfathered analysis access modes.

Revision ID: 20260917_14
Revises: 37a88a68d924
Create Date: 2026-09-17 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260917_14"
down_revision: str | Sequence[str] | None = "37a88a68d924"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_cases",
        sa.Column(
            "access_mode",
            sa.String(length=30),
            server_default="standard",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_analysis_cases_access_mode",
        "analysis_cases",
        "access_mode IN ('standard', 'free_preview', 'grandfathered')",
    )

    # Cases analyzed before billing was introduced must keep their documents
    # and results. They become permanently unlocked without fabricating a
    # Stripe purchase or an analysis credit.
    op.execute(
        """
        UPDATE analysis_cases AS analysis_case
        SET access_mode = 'grandfathered'
        WHERE NOT EXISTS (
            SELECT 1
            FROM analysis_accesses AS access
            WHERE access.analysis_case_id = analysis_case.id
        )
        AND (
            EXISTS (
                SELECT 1
                FROM reports AS report
                WHERE report.analysis_case_id = analysis_case.id
            )
            OR EXISTS (
                SELECT 1
                FROM documents AS document
                WHERE document.analysis_case_id = analysis_case.id
                  AND document.status = 'completed'
            )
        )
        """
    )

    op.create_index(
        "uq_analysis_cases_one_free_preview_per_user",
        "analysis_cases",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("access_mode = 'free_preview'"),
        sqlite_where=sa.text("access_mode = 'free_preview'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_analysis_cases_one_free_preview_per_user",
        table_name="analysis_cases",
    )
    op.drop_constraint(
        "ck_analysis_cases_access_mode",
        "analysis_cases",
        type_="check",
    )
    op.drop_column("analysis_cases", "access_mode")
