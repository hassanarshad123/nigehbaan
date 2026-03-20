"""Add statistical_reports and transparency_reports tables.

Revision ID: 002
Revises: 001
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "statistical_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("report_year", sa.Integer(), nullable=True),
        sa.Column("report_title", sa.Text(), nullable=True),
        sa.Column("indicator", sa.String(200), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("geographic_scope", sa.String(100), nullable=True),
        sa.Column("district_pcode", sa.String(20), nullable=True),
        sa.Column("victim_gender", sa.String(20), nullable=True),
        sa.Column("victim_age_bracket", sa.String(30), nullable=True),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("local_pdf_path", sa.Text(), nullable=True),
        sa.Column("extraction_method", sa.String(50), nullable=True),
        sa.Column("extraction_confidence", sa.Float(), nullable=True),
        sa.Column("raw_table_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_name", "report_year", "indicator", "geographic_scope",
            name="uq_stat_report_source_year_indicator_geo",
        ),
    )
    op.create_index("ix_statistical_reports_source_name", "statistical_reports", ["source_name"])
    op.create_index("ix_statistical_reports_district_pcode", "statistical_reports", ["district_pcode"])

    op.create_table(
        "transparency_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("platform", sa.String(100), nullable=False),
        sa.Column("report_period", sa.String(50), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="Pakistan"),
        sa.Column("metric", sa.String(200), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "platform", "report_period", "country", "metric",
            name="uq_transparency_platform_period_country_metric",
        ),
    )
    op.create_index("ix_transparency_reports_platform", "transparency_reports", ["platform"])


def downgrade() -> None:
    op.drop_table("transparency_reports")
    op.drop_table("statistical_reports")
