"""Add tenant_group_name to tenant table

Revision ID: 4f3d1b9e8a21
Revises: a22d9d209f01
Create Date: 2026-01-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

from open_webui.internal.db import get_table_name


revision = "4f3d1b9e8a21"
down_revision = "a22d9d209f01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = get_table_name("tenant")
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    if "tenant_group_name" not in columns:
        op.add_column(
            table_name,
            sa.Column("tenant_group_name", sa.String(length=255), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = get_table_name("tenant")
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    if "tenant_group_name" in columns:
        op.drop_column(table_name, "tenant_group_name")
