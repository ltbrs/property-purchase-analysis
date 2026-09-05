"""Persist the user review status of analysis findings.

Revision ID: 20260830_08
Revises: 20260828_07
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260830_08"
down_revision: str | Sequence[str] | None = "20260828_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "risk_findings",
        sa.Column(
            "review_status",
            sa.String(length=20),
            nullable=False,
            server_default="open",
        ),
    )
    op.create_check_constraint(
        "ck_risk_findings_review_status",
        "risk_findings",
        "review_status IN ('open', 'not_problematic')",
    )
    op.alter_column("risk_findings", "review_status", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_risk_findings_review_status", "risk_findings", type_="check")
    op.drop_column("risk_findings", "review_status")
