"""Backfill work hours defaults

Revision ID: b3a7c2d9e4f1
Revises: f4b2c9e0d1a7
Create Date: 2025-03-13 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b3a7c2d9e4f1"
down_revision = "f4b2c9e0d1a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE \"user\" SET work_days = '1,2,3,4,5', "
        "work_hours_start = '09:00', work_hours_end = '17:00' "
        "WHERE work_days IS NULL OR work_hours_start IS NULL OR work_hours_end IS NULL"
    )
    op.alter_column(
        "user",
        "work_days",
        existing_type=sa.String(length=20),
        server_default="1,2,3,4,5",
        existing_nullable=True,
    )
    op.alter_column(
        "user",
        "work_hours_start",
        existing_type=sa.String(length=5),
        server_default="09:00",
        existing_nullable=True,
    )
    op.alter_column(
        "user",
        "work_hours_end",
        existing_type=sa.String(length=5),
        server_default="17:00",
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "user",
        "work_hours_end",
        existing_type=sa.String(length=5),
        server_default=None,
        existing_nullable=True,
    )
    op.alter_column(
        "user",
        "work_hours_start",
        existing_type=sa.String(length=5),
        server_default=None,
        existing_nullable=True,
    )
    op.alter_column(
        "user",
        "work_days",
        existing_type=sa.String(length=20),
        server_default=None,
        existing_nullable=True,
    )
