"""Add the property type to analysis cases.

Revision ID: 20260828_06
Revises: 20260826_05
Create Date: 2026-08-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260828_06"
down_revision: str | Sequence[str] | None = "20260826_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_cases",
        sa.Column(
            "property_type",
            sa.String(length=30),
            server_default="unknown",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_analysis_cases_property_type",
        "analysis_cases",
        "property_type IN ('unknown', 'apartment_coproperty', 'house')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_analysis_cases_property_type", "analysis_cases", type_="check"
    )
    op.drop_column("analysis_cases", "property_type")
