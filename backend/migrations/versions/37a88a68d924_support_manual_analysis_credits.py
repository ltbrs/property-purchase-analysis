"""Support traceable manual analysis credits.

Revision ID: 37a88a68d924
Revises: 1eab66a033b4
Create Date: 2026-09-16 22:58:04.533344
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "37a88a68d924"
down_revision: str | Sequence[str] | None = "1eab66a033b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_credits",
        sa.Column(
            "source",
            sa.String(length=30),
            server_default="stripe_purchase",
            nullable=False,
        ),
    )
    op.add_column(
        "analysis_credits",
        sa.Column("grant_note", sa.String(length=500), nullable=True),
    )
    op.alter_column(
        "analysis_credits",
        "purchase_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.create_check_constraint(
        "ck_analysis_credits_source",
        "analysis_credits",
        "(source = 'stripe_purchase' AND purchase_id IS NOT NULL "
        "AND grant_note IS NULL) OR "
        "(source = 'manual_grant' AND purchase_id IS NULL "
        "AND length(trim(grant_note)) > 0)",
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM analysis_credits WHERE source = 'manual_grant'
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade while manual analysis credits exist';
            END IF;
        END
        $$
        """
    )
    op.drop_constraint(
        "ck_analysis_credits_source",
        "analysis_credits",
        type_="check",
    )
    op.alter_column(
        "analysis_credits",
        "purchase_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.drop_column("analysis_credits", "grant_note")
    op.drop_column("analysis_credits", "source")
