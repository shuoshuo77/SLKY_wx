"""Index the public base listing query.

Revision ID: 20260712_0003
Revises: 20260712_0002
"""
from alembic import op

revision = "20260712_0003"
down_revision = "20260712_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_forest_bases_status_created",
        "forest_bases",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_forest_bases_status_created",
        table_name="forest_bases",
    )
