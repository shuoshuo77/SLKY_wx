"""Expand policy and industry content columns.

Revision ID: 20260712_0002
Revises: 20260712_0001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "20260712_0002"
down_revision = "20260712_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite does not support MySQL's LONGTEXT and does not enforce VARCHAR
    # lengths, so the initial TEXT-affinity columns already accept this data.
    if op.get_bind().dialect.name == "sqlite":
        return
    op.alter_column(
        "policies",
        "content",
        existing_type=sa.String(length=300),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "industry_data",
        "content",
        existing_type=sa.String(length=300),
        type_=mysql.LONGTEXT(),
        existing_nullable=True,
    )


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        return
    op.alter_column(
        "industry_data",
        "content",
        existing_type=mysql.LONGTEXT(),
        type_=sa.String(length=300),
        existing_nullable=True,
    )
    op.alter_column(
        "policies",
        "content",
        existing_type=mysql.LONGTEXT(),
        type_=sa.String(length=300),
        existing_nullable=True,
    )
