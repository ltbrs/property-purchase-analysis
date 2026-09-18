"""add global demo case

Revision ID: 1c439cb1ee8b
Revises: 20260917_14
Create Date: 2026-09-18 13:44:20.838066
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1c439cb1ee8b"
down_revision: str | Sequence[str] | None = "20260917_14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("show_demo_case", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "analysis_cases",
        sa.Column("case_kind", sa.String(length=20), server_default="user", nullable=False),
    )
    op.add_column(
        "analysis_cases",
        sa.Column("template_key", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "analysis_cases",
        sa.Column("template_manifest_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "analysis_cases",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("analysis_cases", "user_id", existing_type=sa.Uuid(), nullable=True)

    op.create_check_constraint(
        "ck_analysis_cases_case_kind",
        "analysis_cases",
        "case_kind IN ('user', 'demo')",
    )
    op.create_check_constraint(
        "ck_analysis_cases_kind_fields",
        "analysis_cases",
        "(case_kind = 'user' AND user_id IS NOT NULL "
        "AND template_key IS NULL AND template_manifest_sha256 IS NULL "
        "AND published_at IS NULL) OR "
        "(case_kind = 'demo' AND user_id IS NULL "
        "AND template_key IS NOT NULL AND template_manifest_sha256 IS NOT NULL "
        "AND access_mode = 'grandfathered')",
    )
    op.create_check_constraint(
        "ck_analysis_cases_template_manifest_sha256_length",
        "analysis_cases",
        "template_manifest_sha256 IS NULL OR length(template_manifest_sha256) = 64",
    )

    op.drop_index(
        "uq_analysis_cases_one_free_preview_per_user",
        table_name="analysis_cases",
    )
    op.create_index(
        "uq_analysis_cases_one_free_preview_per_user",
        "analysis_cases",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("access_mode = 'free_preview' AND case_kind = 'user'"),
        sqlite_where=sa.text("access_mode = 'free_preview' AND case_kind = 'user'"),
    )
    op.create_index(
        "uq_analysis_cases_demo_template_key",
        "analysis_cases",
        ["template_key"],
        unique=True,
        postgresql_where=sa.text("case_kind = 'demo'"),
        sqlite_where=sa.text("case_kind = 'demo'"),
    )
    op.create_index(
        "uq_analysis_cases_one_published_demo",
        "analysis_cases",
        ["case_kind"],
        unique=True,
        postgresql_where=sa.text("case_kind = 'demo' AND published_at IS NOT NULL"),
        sqlite_where=sa.text("case_kind = 'demo' AND published_at IS NOT NULL"),
    )


def downgrade() -> None:
    op.execute("DELETE FROM analysis_cases WHERE case_kind = 'demo'")
    op.drop_index("uq_analysis_cases_one_published_demo", table_name="analysis_cases")
    op.drop_index("uq_analysis_cases_demo_template_key", table_name="analysis_cases")
    op.drop_index(
        "uq_analysis_cases_one_free_preview_per_user",
        table_name="analysis_cases",
    )
    op.create_index(
        "uq_analysis_cases_one_free_preview_per_user",
        "analysis_cases",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("access_mode = 'free_preview'"),
        sqlite_where=sa.text("access_mode = 'free_preview'"),
    )
    op.drop_constraint(
        "ck_analysis_cases_template_manifest_sha256_length",
        "analysis_cases",
        type_="check",
    )
    op.drop_constraint("ck_analysis_cases_kind_fields", "analysis_cases", type_="check")
    op.drop_constraint("ck_analysis_cases_case_kind", "analysis_cases", type_="check")
    op.alter_column("analysis_cases", "user_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_column("analysis_cases", "published_at")
    op.drop_column("analysis_cases", "template_manifest_sha256")
    op.drop_column("analysis_cases", "template_key")
    op.drop_column("analysis_cases", "case_kind")
    op.drop_column("users", "show_demo_case")
