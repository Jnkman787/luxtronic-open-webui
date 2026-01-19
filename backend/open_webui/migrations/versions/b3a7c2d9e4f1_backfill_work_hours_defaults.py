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
    # Use SQLAlchemy table construct for dialect-agnostic quoting
    user_table = sa.table(
        "user",
        sa.column("work_days"),
        sa.column("work_hours_start"),
        sa.column("work_hours_end"),
    )
    op.execute(
        user_table.update()
        .where(
            sa.or_(
                user_table.c.work_days.is_(None),
                user_table.c.work_hours_start.is_(None),
                user_table.c.work_hours_end.is_(None),
            )
        )
        .values(
            work_days="1,2,3,4,5",
            work_hours_start="09:00",
            work_hours_end="17:00",
        )
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
