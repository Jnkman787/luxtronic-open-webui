"""Add saved_item table for My Stuff dashboard

Revision ID: a1b2c3d4e5f6
Revises: a22d9d209f01
Create Date: 2026-01-27 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from open_webui.internal.db import get_table_name
from open_webui.migrations.util import get_existing_tables

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "a22d9d209f01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())
    table_name = get_table_name("saved_item")

    if table_name not in existing_tables:
        op.create_table(
            table_name,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(255), nullable=False),
            sa.Column("chat_id", sa.String(255), nullable=True),
            sa.Column("message_id", sa.String(255), nullable=False),
            sa.Column("type", sa.String(50), nullable=False),  # line, bar, pie, scatter
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("display_order", sa.Integer, nullable=True),
            sa.Column("sql_template", sa.Text, nullable=False),
            sa.Column("series_config", sa.JSON, nullable=True),
            sa.Column("timeframe_type", sa.String(20), nullable=False),  # days, hours
            sa.Column("timeframe_value", sa.Integer, nullable=False),
            sa.Column("created_at", sa.BigInteger, nullable=False),
            sa.Column("updated_at", sa.BigInteger, nullable=False),
            sa.UniqueConstraint("user_id", "message_id", name=f"uq_{table_name}_user_message"),
        )
        # Add index for user_id queries
        op.create_index(
            f"ix_{table_name}_user_id",
            table_name,
            ["user_id"],
        )


def downgrade() -> None:
    table_name = get_table_name("saved_item")
    op.drop_index(f"ix_{table_name}_user_id", table_name=table_name)
    op.drop_table(table_name)
