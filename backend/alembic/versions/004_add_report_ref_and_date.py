"""Add reference_number and incident_date to public_reports.

Revision ID: 004
Revises: 003
Create Date: 2026-03-23
"""

import sqlalchemy as sa

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add columns as nullable
    op.add_column(
        "public_reports",
        sa.Column("reference_number", sa.String(20), nullable=True),
    )
    op.add_column(
        "public_reports",
        sa.Column("incident_date", sa.Date(), nullable=True),
    )

    # Step 2: Backfill existing rows with generated reference numbers
    op.execute(
        "UPDATE public_reports "
        "SET reference_number = 'NGB-' || UPPER(SUBSTRING(MD5(id::text), 1, 8)) "
        "WHERE reference_number IS NULL"
    )

    # Step 3: Make reference_number NOT NULL after backfill
    op.alter_column("public_reports", "reference_number", nullable=False)

    # Step 4: Add unique index
    op.create_index(
        "ix_public_reports_reference_number",
        "public_reports",
        ["reference_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_public_reports_reference_number", table_name="public_reports")
    op.drop_column("public_reports", "incident_date")
    op.drop_column("public_reports", "reference_number")
