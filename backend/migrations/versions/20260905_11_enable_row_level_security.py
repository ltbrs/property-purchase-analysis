"""Enable row-level security for application tables.

Revision ID: 20260905_11
Revises: 20260902_10
Create Date: 2026-09-05
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260905_11"
down_revision: str | Sequence[str] | None = "20260902_10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APPLICATION_TABLES = (
    "analysis_cases",
    "auth_accounts",
    "contact_submissions",
    "document_classifications",
    "document_extraction_pages",
    "document_extractions",
    "documents",
    "dpe_extractions",
    "reports",
    "risk_findings",
    "structured_extractions",
    "users",
)


def upgrade() -> None:
    # There are intentionally no browser-facing policies. The FastAPI backend is
    # the only data access boundary and connects with the table-owner role.
    for table_name in APPLICATION_TABLES:
        op.execute(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    for table_name in APPLICATION_TABLES:
        op.execute(f'ALTER TABLE "{table_name}" DISABLE ROW LEVEL SECURITY')
