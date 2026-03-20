"""Add court judgment constraints and indices.

Revision ID: 003
Revises: 002
Create Date: 2026-03-20
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_court_judgment_source_url",
        "court_judgments",
        ["source_url"],
    )
    op.create_index(
        "ix_court_judgments_is_trafficking_related",
        "court_judgments",
        ["is_trafficking_related"],
    )


def downgrade() -> None:
    op.drop_index("ix_court_judgments_is_trafficking_related", table_name="court_judgments")
    op.drop_constraint("uq_court_judgment_source_url", "court_judgments", type_="unique")
