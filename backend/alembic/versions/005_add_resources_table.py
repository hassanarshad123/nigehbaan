# ruff: noqa: E501
"""Add resources table and seed with helpline/NGO data.

Revision ID: 005
Revises: 004
Create Date: 2026-03-23
"""

import sqlalchemy as sa

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

SEED_DATA = [
    ("helpline", "Child Protection & Welfare Bureau", "Government helpline for child protection emergencies across Pakistan.", "1099", None, 1),
    ("helpline", "Edhi Foundation", "Emergency ambulance, rescue, and welfare services. 24/7 nationwide.", "1098", None, 2),
    ("helpline", "Roshni Helpline", "Counseling and referral service for children and women in distress.", "0800-22444", None, 3),
    ("helpline", "Pakistan Bait-ul-Mal", "Government social safety net for vulnerable populations.", "0800-12345", None, 4),
    ("helpline", "Women Crisis Centre", "Support for women and children facing violence or exploitation.", "0800-22444", None, 5),
    ("legal_aid", "Legal Aid Society", "Free legal representation for underprivileged victims of trafficking and exploitation.", "021-35837825", "https://www.las.org.pk", 1),
    ("legal_aid", "AGHS Legal Aid Cell", "Pro bono legal services for human rights cases, including child trafficking.", "042-35761999", None, 2),
    ("legal_aid", "Digital Rights Foundation", "Legal support for technology-facilitated crimes against children.", "0800-39393", "https://digitalrightsfoundation.pk", 3),
    ("shelter", "Edhi Homes", "Shelter and care for abandoned, orphaned, and at-risk children nationwide.", "1098", None, 1),
    ("shelter", "SOS Children's Villages", "Long-term family-based care for orphaned and abandoned children.", "051-2604841", "https://www.sos.org.pk", 2),
    ("shelter", "Dar-ul-Aman Shelter Homes", "Government-run shelter homes for women and children in distress.", "Contact local district office", None, 3),
    ("ngo", "SPARC", "Research, advocacy, and direct services for child rights in Pakistan.", "051-2278596", "https://www.sparcpk.org", 1),
    ("ngo", "Sahil", "NGO focused on child sexual abuse prevention, research, and data.", "051-2890505", "https://sahil.org", 2),
    ("ngo", "Group Development Pakistan", "Community-based organization working on bonded labor and child labor.", "042-35913308", None, 3),
    ("ngo", "Bachpan Bachao Andolan", "Grassroots campaigns against child labor and trafficking.", "Contact via website", None, 4),
]


def upgrade() -> None:
    resources_table = op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact", sa.String(255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.bulk_insert(
        resources_table,
        [
            {
                "category": row[0],
                "name": row[1],
                "description": row[2],
                "contact": row[3],
                "url": row[4],
                "sort_order": row[5],
            }
            for row in SEED_DATA
        ],
    )


def downgrade() -> None:
    op.drop_table("resources")
