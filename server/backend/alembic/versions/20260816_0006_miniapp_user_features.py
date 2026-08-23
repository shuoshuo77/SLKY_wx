"""Add mini-program appointments and browse history tables.

Revision ID: 20260816_0006
Revises: 20260802_0005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260816_0006"
down_revision = "20260802_0005"
branch_labels = None
depends_on = None


def _id_column():
    """与 app.database.ID_TYPE 保持一致：MySQL 用 BIGINT UNSIGNED，SQLite 用 INTEGER 以支持自增。"""
    return sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql").with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        tables = set(sa.inspect(op.get_bind()).get_table_names())
        if {"base_appointments", "base_browse_history"}.issubset(tables):
            # Revision 0001 creates the current ORM schema for a fresh SQLite
            # database, so these tables already exist in that path.
            return
    op.create_table(
        "base_appointments",
        sa.Column("id", _id_column(), primary_key=True, autoincrement=True),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("base_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("time_slot", sa.String(30), nullable=False),
        sa.Column("people_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("contact_name", sa.String(50), nullable=False),
        sa.Column("contact_phone", sa.String(30), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "confirmed", "cancelled", name="appointment_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["base_id"], ["forest_bases.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_appt_user_status_date", "base_appointments", ["user_id", "status", "visit_date"])
    op.create_index("idx_appt_base_id", "base_appointments", ["base_id"])

    op.create_table(
        "base_browse_history",
        sa.Column("id", _id_column(), primary_key=True, autoincrement=True),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("base_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("viewed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["base_id"], ["forest_bases.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "base_id", name="uk_user_base_browse"),
    )
    op.create_index("idx_browse_user_viewed", "base_browse_history", ["user_id", "viewed_at"])
    op.create_index("idx_browse_base_id", "base_browse_history", ["base_id"])


def downgrade() -> None:
    op.drop_index("idx_browse_base_id", table_name="base_browse_history")
    op.drop_index("idx_browse_user_viewed", table_name="base_browse_history")
    op.drop_table("base_browse_history")

    op.drop_index("idx_appt_base_id", table_name="base_appointments")
    op.drop_index("idx_appt_user_status_date", table_name="base_appointments")
    op.drop_table("base_appointments")
