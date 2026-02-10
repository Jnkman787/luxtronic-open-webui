"""Add work hours to user

Revision ID: f4b2c9e0d1a7
Revises: c1d9a5b8e7f2
Create Date: 2025-03-13 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "f4b2c9e0d1a7"
down_revision = "c1d9a5b8e7f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("work_days", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("work_hours_start", sa.String(length=5), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("work_hours_end", sa.String(length=5), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user", "work_hours_end")
    op.drop_column("user", "work_hours_start")
    op.drop_column("user", "work_days")
