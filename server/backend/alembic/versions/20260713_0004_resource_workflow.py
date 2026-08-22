"""Add resource review workflow fields.

Revision ID: 20260713_0004
Revises: 20260712_0003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260713_0004"
down_revision = "20260712_0003"
branch_labels = None
depends_on = None

TABLES = ("policies", "natural_resources", "industry_data", "experts")
OLD_ENUMS = {
    "policies": ("draft", "published", "archived"),
    "natural_resources": ("draft", "published"),
    "industry_data": ("draft", "published"),
    "experts": ("draft", "published"),
}
NEW_ENUM = sa.Enum("draft", "pending", "published", "rejected", "archived")


def upgrade() -> None:
    for table in TABLES:
        inspector = sa.inspect(op.get_bind())
        columns = {column["name"] for column in inspector.get_columns(table)}
        foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys(table)}
        indexes = {index["name"] for index in inspector.get_indexes(table)}
        op.alter_column(
            table,
            "status",
            existing_type=sa.Enum(*OLD_ENUMS[table]),
            type_=NEW_ENUM,
            existing_nullable=False,
        )
        if "reviewed_by" not in columns:
            op.add_column(table, sa.Column("reviewed_by", mysql.BIGINT(unsigned=True), nullable=True))
        else:
            op.alter_column(
                table,
                "reviewed_by",
                existing_type=sa.BigInteger(),
                type_=mysql.BIGINT(unsigned=True),
                existing_nullable=True,
            )
        if "reviewed_at" not in columns:
            op.add_column(table, sa.Column("reviewed_at", sa.DateTime(), nullable=True))
        if "reject_reason" not in columns:
            op.add_column(table, sa.Column("reject_reason", sa.Text(), nullable=True))
        fk_name = f"fk_{table}_reviewed_by_users"
        if fk_name not in foreign_keys:
            op.create_foreign_key(
                fk_name,
                table,
                "users",
                ["reviewed_by"],
                ["id"],
            )
        index_name = f"idx_{table}_status_created"
        if index_name not in indexes:
            op.create_index(index_name, table, ["status", "created_at"])


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(sa.text(
            f"UPDATE {table} SET status = 'draft' "
            "WHERE status IN ('pending', 'rejected', 'archived')"
            if table != "policies"
            else f"UPDATE {table} SET status = 'draft' WHERE status IN ('pending', 'rejected')"
        ))
        op.drop_index(f"idx_{table}_status_created", table_name=table)
        op.drop_constraint(f"fk_{table}_reviewed_by_users", table, type_="foreignkey")
        op.drop_column(table, "reject_reason")
        op.drop_column(table, "reviewed_at")
        op.drop_column(table, "reviewed_by")
        op.alter_column(
            table,
            "status",
            existing_type=NEW_ENUM,
            type_=sa.Enum(*OLD_ENUMS[table]),
            existing_nullable=False,
        )
