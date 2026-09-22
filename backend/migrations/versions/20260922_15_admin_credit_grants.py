"""Restrict admin accounts and attribute manually granted credits.

Revision ID: 20260922_15
Revises: 1c439cb1ee8b
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_15"
down_revision: str | Sequence[str] | None = "1c439cb1ee8b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_check_constraint(
        "ck_users_admin_email",
        "users",
        "NOT is_admin OR (email = 'lambertbruyas@gmail.com' AND email_verified)",
    )
    op.add_column(
        "analysis_credits",
        sa.Column("granted_by_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_analysis_credits_granted_by_user_id_users",
        "analysis_credits",
        "users",
        ["granted_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_analysis_credits_granted_by_user_id_users",
        "analysis_credits",
        type_="foreignkey",
    )
    op.drop_column("analysis_credits", "granted_by_user_id")
    op.drop_constraint("ck_users_admin_email", "users", type_="check")
    op.drop_column("users", "is_admin")
