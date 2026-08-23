"""Harden mini-app appointment workflow.

Revision ID: 20260823_0007
Revises: 20260816_0006
"""
from alembic import op
import sqlalchemy as sa


revision = "20260823_0007"
down_revision = "20260816_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("base_appointments")}
        if {"idempotency_key", "status_note"}.issubset(columns):
            # Fresh SQLite schemas are created from the current ORM metadata.
            return
    with op.batch_alter_table("base_appointments") as batch:
        batch.add_column(sa.Column("idempotency_key", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("status_note", sa.String(length=500), nullable=True))
        if dialect == "mysql":
            batch.alter_column(
                "status",
                existing_type=sa.Enum("pending", "confirmed", "cancelled", name="appointment_status"),
                type_=sa.Enum("pending", "confirmed", "cancelled", "rejected", name="appointment_status"),
                existing_nullable=False,
            )
        batch.create_unique_constraint("uq_appointment_user_idempotency", ["user_id", "idempotency_key"])


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    with op.batch_alter_table("base_appointments") as batch:
        batch.drop_constraint("uq_appointment_user_idempotency", type_="unique")
        batch.drop_column("status_note")
        batch.drop_column("idempotency_key")
        if dialect == "mysql":
            batch.alter_column(
                "status",
                existing_type=sa.Enum("pending", "confirmed", "cancelled", "rejected", name="appointment_status"),
                type_=sa.Enum("pending", "confirmed", "cancelled", name="appointment_status"),
                existing_nullable=False,
            )
