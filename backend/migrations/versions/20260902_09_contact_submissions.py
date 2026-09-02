"""Store contact submissions.

Revision ID: 20260902_09
Revises: 20260830_08
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260902_09"
down_revision: str | Sequence[str] | None = "20260830_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contact_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("subject", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="new", nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=False),
        sa.Column("privacy_consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "subject IN ('product', 'analysis', 'pricing', 'privacy', 'technical', "
            "'partnership', 'other')",
            name="ck_contact_submissions_subject",
        ),
        sa.CheckConstraint(
            "status IN ('new', 'archived')",
            name="ck_contact_submissions_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contact_submissions_status_created_at",
        "contact_submissions",
        ["status", "created_at"],
    )

def downgrade() -> None:
    op.drop_index("ix_contact_submissions_status_created_at", table_name="contact_submissions")
    op.drop_table("contact_submissions")
