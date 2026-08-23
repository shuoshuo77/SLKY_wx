"""Add mini-program homepage content and structured extension fields.

Revision ID: 20260802_0005
Revises: 20260713_0004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260802_0005"
down_revision = "20260713_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        inspector = sa.inspect(op.get_bind())
        required_columns = {
            "forest_bases": {"tags", "source_url"},
            "base_resources": {"average_temperature"},
            "base_business": {"partner_institutions", "investment_needs"},
            "natural_resources": {"address", "health_value", "traffic_accessibility", "development_status", "resource_details", "source_url"},
            "industry_data": {"metric_value", "metric_unit", "growth_rate", "sort_order"},
            "policies": {"applicable_region"},
            "experts": {"expert_type", "region", "years_experience", "resume_url", "profile_data"},
        }
        tables = set(inspector.get_table_names())
        if {"banners", "featured_services"}.issubset(tables) and all(
            expected.issubset({column["name"] for column in inspector.get_columns(table)})
            for table, expected in required_columns.items()
        ):
            # A new SQLite database is already created from the current ORM
            # metadata by revision 0001, including these extension fields.
            return

    op.create_table(
        "banners",
        sa.Column("id", mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("subtitle", sa.String(500), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("link_type", sa.String(30), nullable=False, server_default="none"),
        sa.Column("link_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("link_url", sa.String(500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL", name="fk_banners_created_by"),
    )
    op.create_index("idx_banners_active_sort", "banners", ["is_active", "sort_order"])
    op.create_index("idx_banners_schedule", "banners", ["starts_at", "ends_at"])

    op.create_table(
        "featured_services",
        sa.Column("id", mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("icon", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("link_url", sa.String(500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], ondelete="SET NULL", name="fk_featured_services_created_by"
        ),
    )
    op.create_index(
        "idx_featured_services_active_sort", "featured_services", ["is_active", "sort_order"]
    )
    op.create_index("idx_featured_services_category", "featured_services", ["category"])

    op.add_column("forest_bases", sa.Column("tags", sa.String(500), nullable=True))
    op.add_column("forest_bases", sa.Column("source_url", sa.String(500), nullable=True))
    op.add_column("base_resources", sa.Column("average_temperature", sa.DECIMAL(5, 2), nullable=True))
    op.add_column("base_business", sa.Column("partner_institutions", sa.Text(), nullable=True))
    op.add_column("base_business", sa.Column("investment_needs", sa.Text(), nullable=True))

    op.add_column("natural_resources", sa.Column("address", sa.String(300), nullable=True))
    op.add_column("natural_resources", sa.Column("health_value", sa.Text(), nullable=True))
    op.add_column("natural_resources", sa.Column("traffic_accessibility", sa.String(300), nullable=True))
    op.add_column("natural_resources", sa.Column("development_status", sa.String(50), nullable=True))
    op.add_column("natural_resources", sa.Column("resource_details", sa.JSON(), nullable=True))
    op.add_column("natural_resources", sa.Column("source_url", sa.String(500), nullable=True))
    op.create_index(
        "idx_natural_resources_development_status", "natural_resources", ["development_status"]
    )

    op.add_column("industry_data", sa.Column("metric_value", sa.String(100), nullable=True))
    op.add_column("industry_data", sa.Column("metric_unit", sa.String(50), nullable=True))
    op.add_column("industry_data", sa.Column("growth_rate", sa.String(50), nullable=True))
    op.add_column("industry_data", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("idx_industry_data_status_sort", "industry_data", ["status", "sort_order"])

    op.add_column("policies", sa.Column("applicable_region", sa.String(200), nullable=True))
    op.create_index("idx_policies_applicable_region", "policies", ["applicable_region"])

    op.add_column("experts", sa.Column("expert_type", sa.String(50), nullable=True))
    op.add_column("experts", sa.Column("region", sa.String(100), nullable=True))
    op.add_column("experts", sa.Column("years_experience", sa.SmallInteger(), nullable=True))
    op.add_column("experts", sa.Column("resume_url", sa.String(500), nullable=True))
    op.add_column("experts", sa.Column("profile_data", sa.JSON(), nullable=True))
    op.create_index("idx_experts_type_region", "experts", ["expert_type", "region"])


def downgrade() -> None:
    op.drop_index("idx_experts_type_region", table_name="experts")
    for column in ("profile_data", "resume_url", "years_experience", "region", "expert_type"):
        op.drop_column("experts", column)

    op.drop_index("idx_policies_applicable_region", table_name="policies")
    op.drop_column("policies", "applicable_region")

    op.drop_index("idx_industry_data_status_sort", table_name="industry_data")
    for column in ("sort_order", "growth_rate", "metric_unit", "metric_value"):
        op.drop_column("industry_data", column)

    op.drop_index("idx_natural_resources_development_status", table_name="natural_resources")
    for column in (
        "source_url", "resource_details", "development_status", "traffic_accessibility", "health_value", "address"
    ):
        op.drop_column("natural_resources", column)

    for column in ("investment_needs", "partner_institutions"):
        op.drop_column("base_business", column)
    op.drop_column("base_resources", "average_temperature")
    for column in ("source_url", "tags"):
        op.drop_column("forest_bases", column)

    op.drop_index("idx_featured_services_category", table_name="featured_services")
    op.drop_index("idx_featured_services_active_sort", table_name="featured_services")
    op.drop_table("featured_services")
    op.drop_index("idx_banners_schedule", table_name="banners")
    op.drop_index("idx_banners_active_sort", table_name="banners")
    op.drop_table("banners")
