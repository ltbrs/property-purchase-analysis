"""Add the optional analysis case details.

Revision ID: 20260828_07
Revises: 20260828_06
Create Date: 2026-08-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260828_07"
down_revision: str | Sequence[str] | None = "20260828_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_cases", sa.Column("price_eur", sa.Numeric(precision=14, scale=2))
    )
    op.add_column(
        "analysis_cases", sa.Column("surface_m2", sa.Numeric(precision=10, scale=2))
    )
    op.add_column("analysis_cases", sa.Column("lot_count", sa.Integer()))
    op.create_check_constraint(
        "ck_analysis_cases_price_positive",
        "analysis_cases",
        "price_eur IS NULL OR price_eur > 0",
    )
    op.create_check_constraint(
        "ck_analysis_cases_surface_positive",
        "analysis_cases",
        "surface_m2 IS NULL OR surface_m2 > 0",
    )
    op.create_check_constraint(
        "ck_analysis_cases_lot_count_positive",
        "analysis_cases",
        "lot_count IS NULL OR lot_count > 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_analysis_cases_lot_count_positive", "analysis_cases", type_="check"
    )
    op.drop_constraint(
        "ck_analysis_cases_surface_positive", "analysis_cases", type_="check"
    )
    op.drop_constraint(
        "ck_analysis_cases_price_positive", "analysis_cases", type_="check"
    )
    op.drop_column("analysis_cases", "lot_count")
    op.drop_column("analysis_cases", "surface_m2")
    op.drop_column("analysis_cases", "price_eur")
