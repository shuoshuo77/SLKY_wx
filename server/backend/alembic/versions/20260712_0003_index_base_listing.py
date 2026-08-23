"""Index the public base listing query.

Revision ID: 20260712_0003
Revises: 20260712_0002
"""
from alembic import op
import sqlalchemy as sa

revision = "20260712_0003"
down_revision = "20260712_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("forest_bases")}
    if "idx_forest_bases_status_created" in existing:
        return
    op.create_index(
        "idx_forest_bases_status_created",
        "forest_bases",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    existing = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("forest_bases")}
    if "idx_forest_bases_status_created" not in existing:
        return
    op.drop_index(
        "idx_forest_bases_status_created",
        table_name="forest_bases",
    )
