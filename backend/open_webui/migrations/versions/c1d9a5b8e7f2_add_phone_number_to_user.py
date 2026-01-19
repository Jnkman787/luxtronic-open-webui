"""Add phone number to user

Revision ID: c1d9a5b8e7f2
Revises: 7b2f4c6a1e3d
Create Date: 2025-03-13 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c1d9a5b8e7f2"
down_revision = "7b2f4c6a1e3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("phone_number", sa.String(length=25), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user", "phone_number")
