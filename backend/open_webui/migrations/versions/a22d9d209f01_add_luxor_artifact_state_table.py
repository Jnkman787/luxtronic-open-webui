"""Add luxor_artifact_state table

Revision ID: a22d9d209f01
Revises: b3a7c2d9e4f1
Create Date: 2026-01-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from open_webui.internal.db import get_table_name
from open_webui.migrations.util import get_existing_tables

# revision identifiers, used by Alembic.
revision: str = "a22d9d209f01"
down_revision: Union[str, None] = "b3a7c2d9e4f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())
    table_name = get_table_name("luxor_artifact_state")

    if table_name not in existing_tables:
        op.create_table(
            table_name,
            sa.Column("s3_key", sa.String(length=512), nullable=False),
            sa.Column("artifact_uuid", sa.String(length=255), nullable=True),
            sa.Column("ensemble_key", sa.String(length=512), nullable=True),
            sa.Column("faiss_key", sa.String(length=512), nullable=True),
            sa.Column("kg_key", sa.String(length=512), nullable=True),
            sa.Column("build_lock", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("build_scheduled", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "last_built",
                sa.DateTime(),
                nullable=True,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("s3_key"),
        )


def downgrade() -> None:
    op.drop_table(get_table_name("luxor_artifact_state"))
