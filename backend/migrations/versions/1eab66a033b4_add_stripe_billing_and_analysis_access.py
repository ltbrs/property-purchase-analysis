"""Add Stripe purchases, analysis credits, and time-limited case access.

Revision ID: 1eab66a033b4
Revises: 20260913_13
Create Date: 2026-09-16 08:36:56.702170
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1eab66a033b4"
down_revision: str | Sequence[str] | None = "20260913_13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in (
        "document_classifications",
        "dpe_extractions",
        "structured_extractions",
    ):
        op.add_column(
            table_name,
            sa.Column("input_tokens", sa.Integer(), server_default="0", nullable=False),
        )
        op.add_column(
            table_name,
            sa.Column("output_tokens", sa.Integer(), server_default="0", nullable=False),
        )

    op.create_table(
        "stripe_purchases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("offer_code", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("expected_amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("credit_count", sa.Integer(), nullable=False),
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "offer_code IN ('single_analysis', 'search_pack')",
            name="ck_stripe_purchases_offer_code",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'open', 'paid', 'failed', 'expired')",
            name="ck_stripe_purchases_status",
        ),
        sa.CheckConstraint(
            "expected_amount_cents > 0",
            name="ck_stripe_purchases_amount_positive",
        ),
        sa.CheckConstraint(
            "credit_count > 0",
            name="ck_stripe_purchases_credit_count_positive",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_checkout_session_id"),
    )
    op.create_index(
        "ix_stripe_purchases_user_created",
        "stripe_purchases",
        ["user_id", "created_at"],
    )

    op.create_table(
        "analysis_credits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_by_case_id", sa.Uuid(), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_id"], ["stripe_purchases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["consumed_by_case_id"], ["analysis_cases.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analysis_credits_available",
        "analysis_credits",
        ["user_id", "consumed_at", "expires_at"],
    )
    op.create_index(
        "ix_analysis_credits_purchase_id",
        "analysis_credits",
        ["purchase_id"],
    )
    op.create_index(
        "ix_analysis_credits_consumed_case",
        "analysis_credits",
        ["consumed_by_case_id"],
    )

    op.create_table(
        "analysis_accesses",
        sa.Column("analysis_case_id", sa.Uuid(), nullable=False),
        sa.Column("credit_id", sa.Uuid(), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("report_refresh_count", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint(
            "expires_at > activated_at",
            name="ck_analysis_accesses_valid_window",
        ),
        sa.ForeignKeyConstraint(["analysis_case_id"], ["analysis_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["credit_id"], ["analysis_credits.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("analysis_case_id"),
        sa.UniqueConstraint("credit_id", name="uq_analysis_accesses_credit_id"),
    )

    op.create_table(
        "stripe_webhook_events",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    for table_name in (
        "stripe_purchases",
        "analysis_credits",
        "analysis_accesses",
        "stripe_webhook_events",
    ):
        op.execute(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY')
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    REVOKE ALL ON TABLE "{table_name}" FROM anon;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                    REVOKE ALL ON TABLE "{table_name}" FROM authenticated;
                END IF;
            END
            $$
            """
        )


def downgrade() -> None:
    op.drop_table("stripe_webhook_events")
    op.drop_table("analysis_accesses")
    op.drop_index("ix_analysis_credits_consumed_case", table_name="analysis_credits")
    op.drop_index("ix_analysis_credits_purchase_id", table_name="analysis_credits")
    op.drop_index("ix_analysis_credits_available", table_name="analysis_credits")
    op.drop_table("analysis_credits")
    op.drop_index("ix_stripe_purchases_user_created", table_name="stripe_purchases")
    op.drop_table("stripe_purchases")
    for table_name in (
        "structured_extractions",
        "dpe_extractions",
        "document_classifications",
    ):
        op.drop_column(table_name, "output_tokens")
        op.drop_column(table_name, "input_tokens")
