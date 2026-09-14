"""Allow one uploaded PDF to contain multiple classified page segments.

Revision ID: 20260913_13
Revises: 20260912_12
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260913_13"
down_revision: str | Sequence[str] | None = "20260912_12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document_classifications",
        sa.Column("start_page", sa.Integer(), nullable=True),
    )
    op.add_column(
        "document_classifications",
        sa.Column("end_page", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE document_classifications AS classification
        SET start_page = COALESCE((
                SELECT MIN(page.page_number)
                FROM document_extractions AS extraction
                JOIN document_extraction_pages AS page
                  ON page.extraction_id = extraction.id
                WHERE extraction.document_id = classification.document_id
            ), 1),
            end_page = COALESCE((
                SELECT MAX(page.page_number)
                FROM document_extractions AS extraction
                JOIN document_extraction_pages AS page
                  ON page.extraction_id = extraction.id
                WHERE extraction.document_id = classification.document_id
            ), 1)
        """
    )
    op.alter_column("document_classifications", "start_page", nullable=False)
    op.alter_column("document_classifications", "end_page", nullable=False)
    op.drop_constraint(
        "document_classifications_document_id_key",
        "document_classifications",
        type_="unique",
    )
    op.create_check_constraint(
        "ck_classification_page_range",
        "document_classifications",
        "start_page > 0 AND end_page >= start_page",
    )
    op.create_unique_constraint(
        "uq_classification_document_type_pages",
        "document_classifications",
        ["document_id", "document_type", "start_page", "end_page"],
    )


def downgrade() -> None:
    # The former schema can retain only the first segment for each uploaded file.
    op.execute(
        """
        DELETE FROM document_classifications AS classification
        USING document_classifications AS earlier
        WHERE classification.document_id = earlier.document_id
          AND (
            classification.start_page > earlier.start_page
            OR (
              classification.start_page = earlier.start_page
              AND classification.id > earlier.id
            )
          )
        """
    )
    op.drop_constraint(
        "uq_classification_document_type_pages",
        "document_classifications",
        type_="unique",
    )
    op.drop_constraint(
        "ck_classification_page_range",
        "document_classifications",
        type_="check",
    )
    op.drop_column("document_classifications", "end_page")
    op.drop_column("document_classifications", "start_page")
    op.create_unique_constraint(
        "document_classifications_document_id_key",
        "document_classifications",
        ["document_id"],
    )
