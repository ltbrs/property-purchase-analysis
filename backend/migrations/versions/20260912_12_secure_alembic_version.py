"""Enable row-level security for the Alembic version table.

Revision ID: 20260912_12
Revises: 20260905_11
Create Date: 2026-09-12
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260912_12"
down_revision: str | Sequence[str] | None = "20260905_11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Supabase exposes the public schema through its Data API. No browser role
    # needs access to Alembic's internal migration bookkeeping table.
    op.execute('ALTER TABLE "alembic_version" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.execute('ALTER TABLE "alembic_version" DISABLE ROW LEVEL SECURITY')
