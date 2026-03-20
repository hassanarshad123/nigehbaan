"""Initial schema — all 12 tables with indexes.

Revision ID: 001
Revises: None
Create Date: 2026-03-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all 12 tables and their indexes."""

    # Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ── 1. boundaries ─────────────────────────────────────────────────
    op.create_table(
        "boundaries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("admin_level", sa.Integer, nullable=False),
        sa.Column("name_en", sa.String(255), nullable=False),
        sa.Column("name_ur", sa.String(255), nullable=True),
        sa.Column("pcode", sa.String(20), nullable=False, unique=True),
        sa.Column("parent_pcode", sa.String(20), sa.ForeignKey("boundaries.pcode"), nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(geometry_type="MULTIPOLYGON", srid=4326),
            nullable=True,
        ),
        sa.Column("population_total", sa.Integer, nullable=True),
        sa.Column("population_male", sa.Integer, nullable=True),
        sa.Column("population_female", sa.Integer, nullable=True),
        sa.Column("population_urban", sa.Integer, nullable=True),
        sa.Column("population_rural", sa.Integer, nullable=True),
        sa.Column("area_sqkm", sa.Float, nullable=True),
    )
    op.create_index("idx_boundaries_pcode", "boundaries", ["pcode"])
    op.create_index("idx_boundaries_parent", "boundaries", ["parent_pcode"])
    op.create_index("idx_boundaries_admin_level", "boundaries", ["admin_level"])
    op.create_index(
        "idx_boundaries_geom", "boundaries", ["geometry"], postgresql_using="gist"
    )

    # ── 2. district_name_variants ─────────────────────────────────────
    op.create_table(
        "district_name_variants",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("variant_name", sa.String(255), nullable=False),
        sa.Column(
            "canonical_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=False,
        ),
        sa.Column("source", sa.String(100), nullable=True),
        sa.UniqueConstraint("variant_name", "source", name="uq_variant_source"),
    )
    op.create_index("idx_dnv_variant", "district_name_variants", ["variant_name"])
    op.create_index("idx_dnv_pcode", "district_name_variants", ["canonical_pcode"])

    # ── 3. incidents ──────────────────────────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_id", sa.String(100), nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("incident_date", sa.Date, nullable=True),
        sa.Column("report_date", sa.Date, nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("month", sa.Integer, nullable=True),
        sa.Column(
            "district_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=True,
        ),
        sa.Column(
            "province_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=True,
        ),
        sa.Column("location_detail", sa.Text, nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("geocode_confidence", sa.Float, nullable=True),
        sa.Column("incident_type", sa.String(100), nullable=True),
        sa.Column("sub_type", sa.String(100), nullable=True),
        sa.Column("victim_count", sa.Integer, nullable=True),
        sa.Column("victim_gender", sa.String(20), nullable=True),
        sa.Column("victim_age_min", sa.Integer, nullable=True),
        sa.Column("victim_age_max", sa.Integer, nullable=True),
        sa.Column("victim_age_bracket", sa.String(30), nullable=True),
        sa.Column("perpetrator_type", sa.String(100), nullable=True),
        sa.Column("perpetrator_count", sa.Integer, nullable=True),
        sa.Column("fir_registered", sa.Boolean, nullable=True),
        sa.Column("case_status", sa.String(50), nullable=True),
        sa.Column("conviction", sa.Boolean, nullable=True),
        sa.Column("sentence_detail", sa.Text, nullable=True),
        sa.Column("extraction_confidence", sa.Float, nullable=True),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_incidents_year", "incidents", ["year"])
    op.create_index("idx_incidents_district", "incidents", ["district_pcode"])
    op.create_index("idx_incidents_province", "incidents", ["province_pcode"])
    op.create_index("idx_incidents_type", "incidents", ["incident_type"])
    op.create_index("idx_incidents_source_type", "incidents", ["source_type"])
    op.create_index("idx_incidents_geom", "incidents", ["geometry"], postgresql_using="gist")

    # ── 4. brick_kilns ────────────────────────────────────────────────
    op.create_table(
        "brick_kilns",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326),
            nullable=False,
        ),
        sa.Column("kiln_type", sa.String(50), nullable=True),
        sa.Column("nearest_school_m", sa.Float, nullable=True),
        sa.Column("nearest_hospital_m", sa.Float, nullable=True),
        sa.Column("population_1km", sa.Integer, nullable=True),
        sa.Column(
            "district_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=True,
        ),
        sa.Column("source", sa.String(100), nullable=True),
    )
    op.create_index("idx_kilns_district", "brick_kilns", ["district_pcode"])
    op.create_index("idx_kilns_geom", "brick_kilns", ["geometry"], postgresql_using="gist")

    # ── 5. border_crossings ───────────────────────────────────────────
    op.create_table(
        "border_crossings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("border_country", sa.String(100), nullable=True),
        sa.Column("crossing_type", sa.String(50), nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("vulnerability_score", sa.Float, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index(
        "idx_borders_geom", "border_crossings", ["geometry"], postgresql_using="gist"
    )

    # ── 6. trafficking_routes ─────────────────────────────────────────
    op.create_table(
        "trafficking_routes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("route_name", sa.String(255), nullable=True),
        sa.Column(
            "origin_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=True,
        ),
        sa.Column("origin_country", sa.String(100), nullable=True),
        sa.Column(
            "destination_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=True,
        ),
        sa.Column("destination_country", sa.String(100), nullable=True),
        sa.Column("transit_points", JSONB, nullable=True),
        sa.Column(
            "route_geometry",
            geoalchemy2.Geometry(geometry_type="LINESTRING", srid=4326),
            nullable=True,
        ),
        sa.Column("trafficking_type", sa.String(100), nullable=True),
        sa.Column("evidence_source", sa.String(255), nullable=True),
        sa.Column("confidence_level", sa.Float, nullable=True),
        sa.Column("year_documented", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index(
        "idx_routes_geom", "trafficking_routes", ["route_geometry"], postgresql_using="gist"
    )

    # ── 7. court_judgments ────────────────────────────────────────────
    op.create_table(
        "court_judgments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("court_name", sa.String(100), nullable=True),
        sa.Column("court_bench", sa.String(100), nullable=True),
        sa.Column("case_number", sa.String(100), nullable=True),
        sa.Column("judgment_date", sa.Date, nullable=True),
        sa.Column("judge_names", ARRAY(sa.Text), nullable=True),
        sa.Column("appellant", sa.Text, nullable=True),
        sa.Column("respondent", sa.Text, nullable=True),
        sa.Column("ppc_sections", ARRAY(sa.Text), nullable=True),
        sa.Column("statutes", ARRAY(sa.Text), nullable=True),
        sa.Column("is_trafficking_related", sa.Boolean, nullable=True),
        sa.Column("trafficking_type", sa.String(100), nullable=True),
        sa.Column(
            "incident_district_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=True,
        ),
        sa.Column(
            "court_district_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=True,
        ),
        sa.Column("verdict", sa.String(50), nullable=True),
        sa.Column("sentence", sa.Text, nullable=True),
        sa.Column("sentence_years", sa.Float, nullable=True),
        sa.Column("judgment_text", sa.Text, nullable=True),
        sa.Column("pdf_url", sa.Text, nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("nlp_confidence", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_cj_court", "court_judgments", ["court_name"])
    op.create_index("idx_cj_case_number", "court_judgments", ["case_number"])
    op.create_index("idx_cj_judgment_date", "court_judgments", ["judgment_date"])
    op.create_index("idx_cj_district", "court_judgments", ["incident_district_pcode"])
    op.create_index(
        "idx_cj_ppc", "court_judgments", ["ppc_sections"], postgresql_using="gin"
    )
    op.create_index(
        "idx_cj_statutes", "court_judgments", ["statutes"], postgresql_using="gin"
    )

    # ── 8. vulnerability_indicators ───────────────────────────────────
    op.create_table(
        "vulnerability_indicators",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "district_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("school_enrollment_rate", sa.Float, nullable=True),
        sa.Column("school_dropout_rate", sa.Float, nullable=True),
        sa.Column("out_of_school_children", sa.Integer, nullable=True),
        sa.Column("literacy_rate", sa.Float, nullable=True),
        sa.Column("poverty_headcount_ratio", sa.Float, nullable=True),
        sa.Column("food_insecurity_rate", sa.Float, nullable=True),
        sa.Column("child_labor_rate", sa.Float, nullable=True),
        sa.Column("unemployment_rate", sa.Float, nullable=True),
        sa.Column("population_under_18", sa.Integer, nullable=True),
        sa.Column("birth_registration_rate", sa.Float, nullable=True),
        sa.Column("child_marriage_rate", sa.Float, nullable=True),
        sa.Column("refugee_population", sa.Integer, nullable=True),
        sa.Column("brick_kiln_count", sa.Integer, nullable=True),
        sa.Column("brick_kiln_density_per_sqkm", sa.Float, nullable=True),
        sa.Column("distance_to_border_km", sa.Float, nullable=True),
        sa.Column("flood_affected_pct", sa.Float, nullable=True),
        sa.Column("trafficking_risk_score", sa.Float, nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.UniqueConstraint("district_pcode", "year", name="uq_vuln_district_year"),
    )
    op.create_index("idx_vuln_district", "vulnerability_indicators", ["district_pcode"])
    op.create_index("idx_vuln_year", "vulnerability_indicators", ["year"])

    # ── 9. tip_report_annual ──────────────────────────────────────────
    op.create_table(
        "tip_report_annual",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("year", sa.Integer, nullable=False, unique=True),
        sa.Column("tier_ranking", sa.String(20), nullable=True),
        sa.Column("ptpa_investigations", sa.Integer, nullable=True),
        sa.Column("ptpa_prosecutions", sa.Integer, nullable=True),
        sa.Column("ptpa_convictions", sa.Integer, nullable=True),
        sa.Column("ptpa_sex_trafficking_inv", sa.Integer, nullable=True),
        sa.Column("ptpa_forced_labor_inv", sa.Integer, nullable=True),
        sa.Column("ppc_investigations", sa.Integer, nullable=True),
        sa.Column("ppc_prosecutions", sa.Integer, nullable=True),
        sa.Column("ppc_convictions", sa.Integer, nullable=True),
        sa.Column("victims_identified", sa.Integer, nullable=True),
        sa.Column("victims_referred", sa.Integer, nullable=True),
        sa.Column("budget_allocated_pkr", sa.Float, nullable=True),
        sa.Column("key_findings", sa.Text, nullable=True),
        sa.Column("recommendations", sa.Text, nullable=True),
        sa.Column("named_hotspots", ARRAY(sa.Text), nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
    )
    op.create_index("idx_tip_year", "tip_report_annual", ["year"])

    # ── 10. public_reports ────────────────────────────────────────────
    op.create_table(
        "public_reports",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column(
            "district_pcode",
            sa.String(20),
            sa.ForeignKey("boundaries.pcode"),
            nullable=True,
        ),
        sa.Column("address_detail", sa.Text, nullable=True),
        sa.Column("photos", JSONB, nullable=True),
        sa.Column("reporter_name", sa.String(255), nullable=True),
        sa.Column("reporter_contact", sa.String(255), nullable=True),
        sa.Column("is_anonymous", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("referred_to", sa.String(255), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_pr_district", "public_reports", ["district_pcode"])
    op.create_index("idx_pr_status", "public_reports", ["status"])
    op.create_index(
        "idx_pr_geom", "public_reports", ["geometry"], postgresql_using="gist"
    )

    # ── 11. news_articles ─────────────────────────────────────────────
    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("url", sa.Text, nullable=False, unique=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("published_date", sa.Date, nullable=True),
        sa.Column("extracted_incidents", JSONB, nullable=True),
        sa.Column("extracted_locations", JSONB, nullable=True),
        sa.Column("extracted_entities", JSONB, nullable=True),
        sa.Column("is_trafficking_relevant", sa.Boolean, nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column("full_text", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_na_source", "news_articles", ["source_name"])
    op.create_index("idx_na_pubdate", "news_articles", ["published_date"])
    op.create_index("idx_na_url", "news_articles", ["url"])
    op.create_index(
        "idx_na_entities", "news_articles", ["extracted_entities"], postgresql_using="gin"
    )

    # ── 12. data_sources ──────────────────────────────────────────────
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("priority", sa.Integer, nullable=True),
        sa.Column("last_scraped", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scraper_name", sa.String(100), nullable=True),
        sa.Column("record_count", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("data_sources")
    op.drop_table("news_articles")
    op.drop_table("public_reports")
    op.drop_table("tip_report_annual")
    op.drop_table("vulnerability_indicators")
    op.drop_table("court_judgments")
    op.drop_table("trafficking_routes")
    op.drop_table("border_crossings")
    op.drop_table("brick_kilns")
    op.drop_table("incidents")
    op.drop_table("district_name_variants")
    op.drop_table("boundaries")
    op.execute("DROP EXTENSION IF EXISTS postgis")
